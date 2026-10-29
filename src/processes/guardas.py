"""Condiciones y efectos reutilizables por las definiciones de proceso."""

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower

from .catalogo import Afectacion
from .motor import registrar


def _vacio(valor):
    return valor is None or (isinstance(valor, str) and not valor.strip())


def requiere(*campos):
    """Campos del detalle (o «ticket.x») obligatorios para salir del estado."""

    def guarda(ctx):
        faltan = []
        for nombre in campos:
            objetivo, campo = (ctx.ticket, nombre[7:]) if nombre.startswith("ticket.") else (
                ctx.detalle, nombre
            )
            attname = objetivo._meta.get_field(campo).attname
            if _vacio(getattr(objetivo, attname)):
                faltan.append(campo)
        if faltan:
            raise ValidationError(f"Faltan datos obligatorios: {', '.join(faltan)}.")

    guarda.__name__ = f"requiere_{'_'.join(campos)}"
    return guarda


def aprobacion_vigente(ctx):
    """La última decisión debe aprobar exactamente el contenido actual."""
    Aprobacion = apps.get_model("processes", "Aprobacion")
    ultima = Aprobacion.objects.filter(
        ticket_id=ctx.ticket.pk, created_at__gte=ctx.ticket.inicio_ciclo_proceso()
    ).order_by("-pk").first()
    if ultima is None or ultima.decision != Aprobacion.Decision.APROBADA:
        raise ValidationError("Se requiere aprobación previa vigente.")
    if ultima.huella != ctx.detalle.huella():
        raise ValidationError(
            "El contenido cambió después de la aprobación; requiere nueva aprobación."
        )


def aprobador_distinto(ctx):
    ticket = ctx.ticket
    if ctx.actor.pk in {ticket.solicitante_id, ticket.creador_id}:
        raise ValidationError("El solicitante no puede aprobar su propia solicitud.")
    beneficiario = getattr(ctx.detalle, "beneficiario_id", None)
    if beneficiario is not None and ctx.actor.pk == beneficiario:
        raise ValidationError("El beneficiario no puede aprobar su propio acceso.")


def ci_o_justificacion(ctx):
    if not ctx.ticket.cis.exists() and _vacio(ctx.ticket.motivo_sin_ci):
        raise ValidationError("Indica los CI afectados o justifica su ausencia.")


def responsable_asignado(ctx):
    if ctx.ticket.responsable_id is None:
        raise ValidationError("El ticket necesita responsable asignado.")


def servicio_activo(ctx):
    if ctx.ticket.servicio.activo is not True:
        raise ValidationError("El servicio solicitado debe existir y estar activo.")


def categoria_evento(*permitidas):
    def guarda(ctx):
        if ctx.detalle.categoria not in permitidas:
            raise ValidationError(
                f"La acción solo aplica a eventos {', '.join(permitidas)}."
            )

    guarda.__name__ = f"categoria_evento_{'_'.join(permitidas)}"
    return guarda


def incidente_vinculado(ctx):
    if ctx.detalle.incidente_id is None:
        raise ValidationError("E2/E3 requieren incidente creado o vinculado.")


def incidentes_relacionados(ctx):
    if not ctx.ticket.relaciones_entrantes.filter(tipo="INCIDENTE_PROBLEMA").exists():
        raise ValidationError("El problema necesita al menos un incidente vinculado.")


def cambio_o_justificacion(ctx):
    tiene_cambio = ctx.ticket.relaciones_salientes.filter(tipo="PROBLEMA_CAMBIO").exists()
    if not tiene_cambio and _vacio(ctx.detalle.justificacion_sin_cambio):
        raise ValidationError(
            "Vincula el cambio correctivo o justifica por qué no se requiere."
        )


def accion_acceso(valor):
    def guarda(ctx):
        if ctx.detalle.accion != valor:
            raise ValidationError(f"La solicitud aprobada no es de {valor.lower()}.")

    guarda.__name__ = f"accion_acceso_{valor}"
    return guarda


def categoria_incidente(ctx):
    detalle = ctx.detalle
    if _vacio(detalle.afectacion) or _vacio(detalle.categoria):
        raise ValidationError("Clasifica afectación y categoría I0–I6.")
    if detalle.categoria != detalle.categoria_sugerida and _vacio(detalle.motivo_categoria):
        raise ValidationError(
            "La categoría difiere de la regla complementaria o no hay sugerencia; "
            "registra el motivo de la clasificación."
        )


def interrupcion_declarada(ctx):
    if ctx.detalle.afectacion == Afectacion.SIN_INTERRUPCION and ctx.detalle.categoria != "I0":
        raise ValidationError("Sin interrupción corresponde a I0.")


def nuevo_servicio_sin_duplicado(ctx):
    detalle = ctx.detalle
    ServicioNivel2 = apps.get_model("catalog", "ServicioNivel2")
    if detalle.modo_resultado == "VINCULAR":
        if detalle.servicio_resultante_id is None:
            raise ValidationError("Indica el servicio existente a vincular.")
        return
    if detalle.modo_resultado != "CREAR":
        raise ValidationError("Indica si el resultado crea o vincula un servicio.")
    faltan = [n for n in ("propuesta_codigo", "propuesta_nombre", "propuesta_nivel1_id",
                          "propuesta_seccion_id") if _vacio(getattr(detalle, n))]
    if faltan:
        raise ValidationError(f"Propuesta de servicio incompleta: {', '.join(faltan)}.")
    duplicado = ServicioNivel2.objects.annotate(nombre_ci=Lower("nombre")).filter(
        nombre_ci=detalle.propuesta_nombre.strip().lower(),
        nivel1_id=detalle.propuesta_nivel1_id,
    )
    if ServicioNivel2.objects.filter(codigo=detalle.propuesta_codigo.strip()).exists() or (
        duplicado.exists()
    ):
        raise ValidationError("Ya existe un servicio con ese código o nombre; vincúlalo.")


def crear_o_vincular_servicio(ctx):
    """Efecto del cierre de nuevos servicios: N2 único creado o vinculado."""
    detalle = ctx.detalle
    if detalle.modo_resultado != "CREAR" or detalle.servicio_resultante_id is not None:
        return
    nuevo_servicio_sin_duplicado(ctx)
    ServicioNivel2 = apps.get_model("catalog", "ServicioNivel2")
    servicio = ServicioNivel2(
        codigo=detalle.propuesta_codigo.strip(), nombre=detalle.propuesta_nombre.strip(),
        nivel1_id=detalle.propuesta_nivel1_id, seccion_responsable_id=detalle.propuesta_seccion_id,
        descripcion=detalle.necesidad, activo=True,
    )
    servicio.save()
    detalle.servicio_resultante = servicio
    detalle.save()
    registrar(ctx.ticket, ctx.actor, "CREAR_SERVICIO", campo="servicio_resultante",
              despues=servicio.pk, motivo=f"Servicio {servicio.codigo} creado.")
