"""Operaciones de aplicación: única vía autorizada para modificar tickets.

Cada operación abre domain_transaction (lock advisory global) y DESPUÉS bloquea
la fila con select_for_update; ese orden fijo evita interbloqueos con los saves
del dominio, que también toman el lock advisory.
"""

from contextlib import contextmanager

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db.models import Q

from accounts.models import Usuario
from config.domain import domain_transaction
from processes.catalogo import (
    EVENTOS_CON_INCIDENTE, Afectacion, CategoriaEvento, Proceso, TipoTicket, proceso_de,
)
from processes.definiciones import DEFINICIONES
from processes.motor import Actor, Contexto, aplicar_campos, ejecutar, registrar
from .adjuntos import validar_archivo
from .models import (
    AdjuntoTicket, ColaServiceDesk, ComentarioTicket, Notificacion, ReclasificacionTicket,
    RelacionTicket, Ticket, TicketCI, TransferenciaTicket, Visibilidad,
)
from .permisos import (
    Capacidad, capacidades, es_solicitante, exigir, exigir_capacidad,
    puede_crear_tickets, puede_escribir, puede_ver, puede_ver_internas,
)


class ConflictoAsignacion(ValidationError):
    """Otro agente ganó el reclamo del ticket."""


@contextmanager
def ticket_bloqueado(ticket_id):
    with domain_transaction():
        ticket = Ticket.objects.select_for_update(of=("self",)).select_related("cola").get(
            pk=ticket_id
        )
        yield ticket


def _exigir_abierto(ticket):
    if not ticket.abierto:
        raise ValidationError("El ticket está cerrado.")


def _texto(valor, mensaje):
    valor = (valor or "").strip()
    if not valor:
        raise ValidationError(mensaje)
    return valor


def crear_ticket(actor, *, tipo, servicio, cola, titulo, descripcion, prioridad, impacto,
                 urgencia, canal, subtipo="", solicitante=None, cis=(), motivo_sin_ci="",
                 detalle=None):
    exigir(puede_crear_tickets(actor), "No puedes registrar tickets.")
    solicitante = solicitante or actor
    proceso = proceso_de(tipo, subtipo)
    if proceso is None:
        raise ValidationError("Tipo/subtipo sin proceso asignado.")
    if solicitante.pk != actor.pk:
        # Registrar en nombre de otro requiere atender la cola destino.
        exigir(Capacidad.ATENDER in capacidades(actor, cola),
               "Solo un agente de la cola registra en nombre de otro solicitante.")
    return _crear_ticket(
        actor, proceso, tipo=tipo, subtipo=subtipo, servicio=servicio, cola=cola,
        titulo=titulo, descripcion=descripcion, prioridad=prioridad, impacto=impacto,
        urgencia=urgencia, canal=canal, solicitante=solicitante, cis=cis,
        motivo_sin_ci=motivo_sin_ci, detalle=detalle,
    )


def _crear_ticket(actor, proceso, *, tipo, subtipo, servicio, cola, titulo, descripcion,
                  prioridad, impacto, urgencia, canal, solicitante, cis, motivo_sin_ci,
                  detalle):
    """Alta sin comprobación de actor: la exige quien la invoca."""
    cis = list(cis)
    if not cis and not (motivo_sin_ci or "").strip():
        raise ValidationError("Asocia al menos un CI o justifica su ausencia.")
    definicion = DEFINICIONES[proceso]
    with domain_transaction():
        ticket = Ticket(
            titulo=titulo, descripcion=descripcion, solicitante=solicitante, creador=actor,
            servicio=servicio, tipo=tipo, subtipo=subtipo, proceso=proceso, cola=cola,
            estado=definicion.estado_inicial, prioridad=prioridad, impacto=impacto,
            urgencia=urgencia, canal=canal, motivo_sin_ci=(motivo_sin_ci or "").strip(),
        )
        ticket.save()
        for ci in cis:
            TicketCI(ticket=ticket, ci=ci, actor=actor).save()
        datos = dict(detalle or {})
        sobrantes = set(datos) - set(definicion.campos_entrada)
        if sobrantes:
            raise ValidationError(f"Datos de alta no admitidos: {sorted(sobrantes)}.")
        detalle_obj = definicion.modelo_detalle()(ticket=ticket, **datos)
        detalle_obj.save()
        registrar(ticket, actor, "CREAR", campo="estado", despues=ticket.estado,
                  motivo=f"{ticket.numero} en cola {cola.codigo}")
        for ci in cis:
            registrar(ticket, actor, "VINCULAR_CI", campo="ci", despues=ci.pk)
        for guarda in definicion.entrada:
            guarda(Contexto(ticket, detalle_obj, actor, datos, ""))
    return ticket


def registrar_evento(actor, *, clave_evento, **kwargs):
    """Idempotente por clave: reprocesar el mismo evento devuelve el existente."""
    from processes.models import DetalleEvento

    clave = _texto(clave_evento, "El evento necesita clave de identidad.")
    with domain_transaction():
        existente = DetalleEvento.objects.filter(clave_evento=clave).first()
        if existente is not None:
            ticket = existente.ticket
            exigir(puede_ver(actor, ticket), "No autorizado.")
            return ticket, False
        detalle = dict(kwargs.pop("detalle", None) or {}, clave_evento=clave)
        ticket = crear_ticket(actor, tipo=TipoTicket.EVENTO, detalle=detalle, **kwargs)
    return ticket, True


def tomar_ticket(actor, ticket_id):
    """Reclamo atómico: con dos agentes simultáneos, solo uno gana."""
    with ticket_bloqueado(ticket_id) as ticket:
        exigir_capacidad(actor, ticket, Capacidad.ATENDER)
        _exigir_abierto(ticket)
        if ticket.responsable_id is not None:
            if ticket.responsable_id == actor.pk:
                return ticket
            raise ConflictoAsignacion("Otro agente ya tomó este ticket.")
        ticket.responsable = actor
        ticket.save()
        registrar(ticket, actor, "TOMAR", campo="responsable", despues=actor.pk)
    return ticket


def asignar_ticket(actor, ticket_id, agente, motivo=""):
    """Asignación manual o reasignación dentro de la misma cola."""
    with ticket_bloqueado(ticket_id) as ticket:
        exigir_capacidad(actor, ticket, Capacidad.TRANSFERIR, Capacidad.ADMINISTRAR)
        _exigir_abierto(ticket)
        anterior = ticket.responsable_id
        if anterior == agente.pk:
            return ticket
        if anterior is not None:
            motivo = _texto(motivo, "La reasignación exige motivo.")
        ticket.responsable = agente
        ticket.save()  # Ticket.clean valida agente activo, no CONSULTA y con ATENDER.
        registrar(ticket, actor, "REASIGNAR" if anterior else "ASIGNAR",
                  campo="responsable", antes=anterior, despues=agente.pk, motivo=motivo)
    return ticket


def liberar_ticket(actor, ticket_id, motivo):
    with ticket_bloqueado(ticket_id) as ticket:
        _exigir_abierto(ticket)
        if ticket.responsable_id != actor.pk:
            exigir_capacidad(actor, ticket, Capacidad.TRANSFERIR, Capacidad.ADMINISTRAR)
        else:
            exigir_capacidad(actor, ticket, Capacidad.ATENDER)
        motivo = _texto(motivo, "Liberar el ticket exige motivo.")
        anterior = ticket.responsable_id
        ticket.responsable = None
        ticket.save()
        registrar(ticket, actor, "LIBERAR", campo="responsable", antes=anterior, motivo=motivo)
    return ticket


def transferir_ticket(actor, ticket_id, cola_destino, motivo, nuevo_responsable=None):
    motivo = _texto(motivo, "La transferencia exige motivo.")
    with ticket_bloqueado(ticket_id) as ticket:
        exigir_capacidad(actor, ticket, Capacidad.TRANSFERIR)
        _exigir_abierto(ticket)
        cola_destino = ColaServiceDesk.objects.get(pk=cola_destino.pk)
        if cola_destino.pk == ticket.cola_id:
            raise ValidationError("La cola destino debe ser distinta de la actual.")
        if cola_destino.proceso != ticket.proceso:
            # SD-DP10: cambiar de proceso sería una reclasificación, no una transferencia.
            raise ValidationError("Solo se transfiere a colas del mismo proceso.")
        if not cola_destino.estado:
            raise ValidationError("La cola destino está inactiva.")
        origen, anterior = ticket.cola, ticket.responsable_id
        ticket.cola = cola_destino
        ticket.responsable = nuevo_responsable
        ticket.save()  # Valida el nuevo responsable contra la cola destino.
        TransferenciaTicket(
            ticket=ticket, cola_origen=origen, cola_destino=cola_destino,
            responsable_anterior_id=anterior, responsable_nuevo=nuevo_responsable,
            actor=actor, motivo=motivo,
        ).save()
        registrar(ticket, actor, "TRANSFERIR", campo="cola", antes=origen.pk,
                  despues=cola_destino.pk, motivo=motivo)
        if anterior != (nuevo_responsable.pk if nuevo_responsable else None):
            registrar(ticket, actor, "TRANSFERIR", campo="responsable", antes=anterior,
                      despues=nuevo_responsable, motivo=motivo)
    return ticket


def _exigir_actor(actor, ticket, transicion):
    exigir(puede_escribir(actor), "La cuenta es de solo lectura.")
    caps = capacidades(actor, ticket.cola)
    atiende = Capacidad.ATENDER in caps and ticket.responsable_id == actor.pk
    if transicion.actor == Actor.ATENDER:
        exigir(atiende, "Solo el agente responsable con capacidad atender ejecuta esta acción.")
    elif transicion.actor == Actor.APROBAR:
        exigir(Capacidad.APROBAR in caps, "Se requiere capacidad aprobar en la cola.")
    elif transicion.actor == Actor.SOLICITANTE:
        exigir(actor.pk == ticket.solicitante_id, "Solo el solicitante ejecuta esta acción.")
    elif transicion.actor == Actor.SOLICITANTE_O_ATENDER:
        exigir(atiende or actor.pk == ticket.solicitante_id, "No autorizado.")
    else:
        raise PermissionDenied("Actor de transición desconocido.")


def ejecutar_accion(actor, ticket_id, accion, motivo="", datos=None):
    with ticket_bloqueado(ticket_id) as ticket:
        definicion = ticket.definicion
        transicion = definicion.transicion(accion, ticket.estado)
        _exigir_actor(actor, ticket, transicion)
        return ejecutar(definicion, ticket, accion, actor, motivo, datos)


def acciones_disponibles(usuario, ticket):
    """Para la interfaz; el servidor vuelve a comprobar en ejecutar_accion."""
    disponibles = []
    for transicion in ticket.definicion.acciones_desde(ticket.estado):
        try:
            _exigir_actor(usuario, ticket, transicion)
        except PermissionDenied:
            continue
        disponibles.append(transicion.accion)
    return disponibles


def actualizar_detalle(actor, ticket_id, datos, motivo=""):
    with ticket_bloqueado(ticket_id) as ticket:
        exigir_capacidad(actor, ticket, Capacidad.ATENDER)
        exigir(ticket.responsable_id == actor.pk, "Solo el responsable actualiza el detalle.")
        _exigir_abierto(ticket)
        definicion = ticket.definicion
        aplicar_campos(ticket, definicion.detalle_de(ticket), actor, dict(datos),
                       definicion.campos_editables, motivo)
    return ticket


def comentar(actor, ticket_id, texto, interno=False):
    with ticket_bloqueado(ticket_id) as ticket:
        exigir(puede_escribir(actor), "La cuenta es de solo lectura.")
        if interno:
            exigir(puede_ver_internas(actor, ticket), "No puedes registrar notas internas.")
        else:
            exigir(es_solicitante(actor, ticket) or puede_ver_internas(actor, ticket),
                   "No puedes comentar este ticket.")
        comentario = ComentarioTicket(
            ticket=ticket, autor=actor, texto=texto,
            visibilidad=Visibilidad.INTERNO if interno else Visibilidad.PUBLICO,
        )
        comentario.save()
        registrar(ticket, actor, "NOTA_INTERNA" if interno else "COMENTARIO",
                  campo="comentario", despues=comentario.pk)
    return comentario


def adjuntar(actor, ticket_id, archivo, interno=False):
    metadatos = validar_archivo(archivo)
    archivo.name = metadatos["nombre_original"]  # La ruta física la genera ruta_adjunto.
    with ticket_bloqueado(ticket_id) as ticket:
        exigir(puede_escribir(actor), "La cuenta es de solo lectura.")
        if interno:
            exigir(puede_ver_internas(actor, ticket), "No puedes adjuntar evidencia interna.")
        else:
            exigir(es_solicitante(actor, ticket) or puede_ver_internas(actor, ticket),
                   "No puedes adjuntar en este ticket.")
        adjunto = AdjuntoTicket(
            ticket=ticket, subido_por=actor, archivo=archivo,
            visibilidad=Visibilidad.INTERNO if interno else Visibilidad.PUBLICO, **metadatos,
        )
        adjunto.save()
        registrar(ticket, actor, "ADJUNTAR", campo="adjunto", despues={
            "id": adjunto.pk, "nombre": adjunto.nombre_original,
            "tamano": adjunto.tamano, "sha256": adjunto.sha256,
        })
    return adjunto


def comentarios_visibles(usuario, ticket):
    exigir(puede_ver(usuario, ticket))
    consulta = ticket.comentarios.all()
    if not puede_ver_internas(usuario, ticket):
        consulta = consulta.filter(visibilidad=Visibilidad.PUBLICO)
    return consulta


def adjuntos_visibles(usuario, ticket):
    exigir(puede_ver(usuario, ticket))
    consulta = ticket.adjuntos.all()
    if not puede_ver_internas(usuario, ticket):
        consulta = consulta.filter(visibilidad=Visibilidad.PUBLICO)
    return consulta


def adjunto_autorizado(usuario, identificador):
    """Conocer la URL no basta: se revalida visibilidad del ticket y del adjunto."""
    try:
        adjunto = AdjuntoTicket.objects.select_related("ticket__cola").get(
            identificador=identificador
        )
    except (ObjectDoesNotExist, ValidationError) as error:
        raise PermissionDenied("Adjunto no disponible.") from error
    exigir(puede_ver(usuario, adjunto.ticket), "Adjunto no disponible.")
    if adjunto.visibilidad == Visibilidad.INTERNO:
        exigir(puede_ver_internas(usuario, adjunto.ticket), "Adjunto no disponible.")
    return adjunto


def vincular_ci(actor, ticket_id, ci, observacion=""):
    with ticket_bloqueado(ticket_id) as ticket:
        exigir_capacidad(actor, ticket, Capacidad.ATENDER)
        _exigir_abierto(ticket)
        if ticket.cis.filter(pk=ci.pk).exists():
            return ticket
        TicketCI(ticket=ticket, ci=ci, actor=actor, observacion=observacion).save()
        registrar(ticket, actor, "VINCULAR_CI", campo="ci", despues=ci.pk, motivo=observacion)
    return ticket


def relacionar_tickets(actor, origen_id, destino_id, tipo, motivo=""):
    with domain_transaction():
        origen = Ticket.objects.select_for_update(of=("self",)).select_related("cola").get(
            pk=origen_id
        )
        destino = Ticket.objects.select_related("cola").get(pk=destino_id)
        exigir_capacidad(actor, origen, Capacidad.ATENDER)
        exigir(puede_ver(actor, destino), "No puedes ver el ticket destino.")
        existente = RelacionTicket.objects.filter(
            origen=origen, destino=destino, tipo=tipo
        ).first()
        if existente:
            return existente
        relacion = RelacionTicket(origen=origen, destino=destino, tipo=tipo, actor=actor,
                                  motivo=motivo)
        relacion.save()
        registrar(origen, actor, "RELACIONAR", campo=tipo, despues=destino.pk, motivo=motivo)
    return relacion


def _cola_incidentes_por_defecto():
    cola = ColaServiceDesk.objects.filter(proceso=Proceso.INCIDENTES, estado=True).order_by(
        "nivel_soporte", "codigo"
    ).first()
    if cola is None:
        raise ValidationError("No hay cola activa de incidentes.")
    return cola


def vincular_incidente_evento(actor, evento_id, incidente_id=None, cola_incidente=None):
    """E2/E3 → incidente nuevo o existente. Repetirlo devuelve el mismo incidente."""
    from processes.models import DetalleEvento

    with ticket_bloqueado(evento_id) as evento:
        exigir_capacidad(actor, evento, Capacidad.ATENDER)
        if evento.proceso != Proceso.EVENTOS:
            raise ValidationError("Solo un evento genera o vincula incidentes.")
        detalle = DetalleEvento.objects.select_for_update().get(ticket_id=evento.pk)
        if detalle.incidente_id is not None:
            if incidente_id is not None and incidente_id != detalle.incidente_id:
                raise ValidationError("El evento ya está vinculado a otro incidente.")
            return detalle.incidente, False
        if detalle.categoria not in EVENTOS_CON_INCIDENTE:
            raise ValidationError("Solo E2/E3 requieren incidente.")
        _exigir_abierto(evento)
        creado = incidente_id is None
        if creado:
            # El agente del evento ya fue autorizado; el incidente hereda sus datos.
            incidente = _crear_ticket(
                actor, Proceso.INCIDENTES, tipo=TipoTicket.INCIDENTE, subtipo="",
                servicio=evento.servicio,
                cola=cola_incidente or _cola_incidentes_por_defecto(),
                titulo=f"Incidente por {evento.numero}: {evento.titulo}"[:200],
                descripcion=evento.descripcion, prioridad=evento.prioridad,
                impacto=evento.impacto, urgencia=evento.urgencia, canal=evento.canal,
                solicitante=evento.solicitante, cis=evento.cis.all(),
                motivo_sin_ci=evento.motivo_sin_ci,
                detalle={"afectacion": Afectacion.SEGURIDAD}
                if detalle.categoria == CategoriaEvento.E3 else {},
            )
        else:
            incidente = Ticket.objects.get(pk=incidente_id)
            exigir(puede_ver(actor, incidente), "No puedes ver el incidente indicado.")
            if incidente.proceso != Proceso.INCIDENTES or not incidente.abierto:
                raise ValidationError("Vincula un incidente abierto.")
        detalle.incidente = incidente
        detalle.save()
        RelacionTicket(origen=evento, destino=incidente, tipo=RelacionTicket.Tipo.EVENTO_INCIDENTE,
                       actor=actor).save()
        Notificacion(
            evento=evento, incidente=incidente, cola=incidente.cola,
            mensaje=f"{evento.numero} ({detalle.categoria}) → {incidente.numero}",
        ).save()
        registrar(evento, actor, "VINCULAR_INCIDENTE", campo="incidente",
                  despues=incidente.pk, motivo="creado" if creado else "existente")
    return incidente, creado


def tickets_en_cola(usuario, cola, incluir_cerrados=False):
    exigir(Capacidad.CONSULTAR in capacidades(usuario, cola), "No puedes consultar la cola.")
    consulta = Ticket.objects.filter(cola=cola)
    if not incluir_cerrados:
        consulta = consulta.abiertos()
    return consulta.en_orden_de_cola()


def siguiente_disponible(usuario, cola):
    return tickets_en_cola(usuario, cola).filter(responsable__isnull=True).first()


def tickets_visibles(usuario):
    """Propios + colas consultables; nunca todo por ser CONSULTA o admin PP2."""
    if not isinstance(usuario, Usuario) or not usuario.is_active:
        return Ticket.objects.none()
    colas = [c.pk for c in ColaServiceDesk.objects.all()
             if Capacidad.CONSULTAR in capacidades(usuario, c)]
    return Ticket.objects.filter(
        Q(solicitante=usuario) | Q(creador=usuario) | Q(cola_id__in=colas)
    ).distinct()


def reclasificar_ticket(actor, ticket_id, *, tipo, cola_destino, motivo, subtipo="",
                        detalle=None):
    """Cambia proceso/tipo de forma explícita: reinicia el flujo y conserva historia."""
    motivo = _texto(motivo, "La reclasificación exige motivo.")
    with ticket_bloqueado(ticket_id) as ticket:
        exigir_capacidad(actor, ticket, Capacidad.TRANSFERIR, Capacidad.ADMINISTRAR)
        _exigir_abierto(ticket)
        proceso = proceso_de(tipo, subtipo)
        if proceso is None:
            raise ValidationError("Tipo/subtipo destino sin proceso.")
        if proceso == ticket.proceso:
            raise ValidationError("Para el mismo proceso usa transferencia, no reclasificación.")
        cola_destino = ColaServiceDesk.objects.get(pk=cola_destino.pk)
        if cola_destino.proceso != proceso or not cola_destino.estado:
            raise ValidationError("La cola destino debe estar activa y pertenecer al proceso.")
        definicion = DEFINICIONES[proceso]
        if definicion.modelo_detalle().objects.filter(ticket_id=ticket.pk).exists():
            raise ValidationError("El ticket ya pasó por ese proceso; abre un ticket nuevo.")
        anterior = {"proceso": ticket.proceso, "tipo": ticket.tipo, "subtipo": ticket.subtipo,
                    "estado": ticket.estado, "cola": ticket.cola}
        responsable = ticket.responsable
        if responsable and Capacidad.ATENDER not in capacidades(responsable, cola_destino):
            responsable = None
        ticket.tipo, ticket.subtipo, ticket.proceso = tipo, subtipo, proceso
        ticket.estado, ticket.cola, ticket.responsable = (
            definicion.estado_inicial, cola_destino, responsable
        )
        ticket.fecha_resolucion = None
        ticket._reclasificacion = True
        ReclasificacionTicket(
            ticket=ticket, proceso_anterior=anterior["proceso"], proceso_nuevo=proceso,
            tipo_anterior=anterior["tipo"], tipo_nuevo=tipo,
            subtipo_anterior=anterior["subtipo"], subtipo_nuevo=subtipo,
            estado_anterior=anterior["estado"], estado_nuevo=definicion.estado_inicial,
            cola_anterior=anterior["cola"], cola_nueva=cola_destino, actor=actor, motivo=motivo,
        ).save()
        ticket.save()
        ticket._reclasificacion = False
        datos = dict(detalle or {})
        sobrantes = set(datos) - set(definicion.campos_entrada)
        if sobrantes:
            raise ValidationError(f"Datos no admitidos: {sorted(sobrantes)}.")
        detalle_obj = definicion.modelo_detalle()(ticket=ticket, **datos)
        detalle_obj.save()
        for guarda in definicion.entrada:
            guarda(Contexto(ticket, detalle_obj, actor, datos, motivo))
        for campo in ("proceso", "tipo", "estado"):
            registrar(ticket, actor, "RECLASIFICAR", campo=campo, antes=anterior[campo],
                      despues=getattr(ticket, campo), motivo=motivo)
        registrar(ticket, actor, "RECLASIFICAR", campo="cola", antes=anterior["cola"].pk,
                  despues=cola_destino.pk, motivo=motivo)
    return ticket
