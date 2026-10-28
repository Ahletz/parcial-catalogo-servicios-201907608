"""Motor de estados compartido; cada proceso aporta su propia definición.

El motor no decide permisos de usuario: service_desk.servicios los exige antes
de invocarlo y mantiene el bloqueo de fila del ticket durante la operación.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Actor(models.TextChoices):
    """Quién puede disparar una transición, además de no ser CONSULTA."""

    ATENDER = "ATENDER", "Agente responsable con capacidad atender"
    APROBAR = "APROBAR", "Aprobador con capacidad aprobar"
    SOLICITANTE = "SOLICITANTE", "Solicitante del ticket"
    SOLICITANTE_O_ATENDER = "SOLICITANTE_O_ATENDER", "Solicitante o agente responsable"


CAMPOS_TICKET = {"resolucion", "prioridad"}


@dataclass(frozen=True)
class Transicion:
    accion: str
    origen: tuple
    destino: str
    actor: str = Actor.ATENDER
    campos: tuple = ()
    guardas: tuple = ()
    efectos: tuple = ()
    requiere_motivo: bool = False
    decision: str = ""


@dataclass(frozen=True)
class DefinicionProceso:
    proceso: str
    detalle: str
    estado_inicial: str
    estados: tuple
    transiciones: tuple
    campos_entrada: tuple = ()
    campos_editables: tuple = ()
    entrada: tuple = ()
    estados_resolucion: frozenset = frozenset()
    estados_con_aprobacion: frozenset = frozenset()
    finales: frozenset = frozenset({"CERRADO"})
    _por_accion: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        for t in self.transiciones:
            desconocidos = (set(t.origen) | {t.destino}) - set(self.estados)
            if desconocidos:
                raise ValueError(f"{self.proceso}.{t.accion}: estados {desconocidos}")
            for origen in t.origen:
                clave = (t.accion, origen)
                if clave in self._por_accion:
                    raise ValueError(f"{self.proceso}: transición repetida {clave}")
                self._por_accion[clave] = t

    def transicion(self, accion, estado):
        t = self._por_accion.get((accion, estado))
        if t is None:
            raise ValidationError(
                f"La acción «{accion}» no es válida en estado {estado} de {self.proceso}."
            )
        return t

    def acciones_desde(self, estado):
        return [t for t in self.transiciones if estado in t.origen]

    def es_transicion(self, origen, destino):
        return any(origen in t.origen and t.destino == destino for t in self.transiciones)

    def modelo_detalle(self):
        return apps.get_model("processes", self.detalle)

    def detalle_de(self, ticket):
        return self.modelo_detalle().objects.get(ticket_id=ticket.pk)


@dataclass
class Contexto:
    ticket: object
    detalle: object
    actor: object
    datos: dict
    motivo: str
    transicion: Transicion | None = None


def serializar(valor):
    if isinstance(valor, models.Model):
        return valor.pk
    if isinstance(valor, timedelta):
        return valor.total_seconds()
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return str(valor)
    return valor


def registrar(ticket, actor, accion, *, campo="", antes=None, despues=None, motivo=""):
    AccionTicket = apps.get_model("service_desk", "AccionTicket")
    AccionTicket(
        ticket=ticket, actor=actor, accion=accion, campo=campo,
        valor_anterior=serializar(antes), valor_nuevo=serializar(despues), motivo=motivo,
    ).save()


def aplicar_campos(ticket, detalle, actor, datos, permitidos, motivo=""):
    """Asigna datos permitidos al detalle/ticket y audita cada diferencia."""
    sobrantes = set(datos) - set(permitidos)
    if sobrantes:
        raise ValidationError(f"Campos no admitidos en esta operación: {sorted(sobrantes)}.")
    cambios_detalle = False
    for nombre, valor in datos.items():
        objetivo = ticket if nombre in CAMPOS_TICKET else detalle
        campo = objetivo._meta.get_field(nombre)
        anterior = getattr(objetivo, campo.attname)
        if campo.is_relation and isinstance(valor, models.Model):
            valor = valor.pk
        if anterior == valor:
            continue
        setattr(objetivo, campo.attname, valor)
        cambios_detalle |= objetivo is detalle
        registrar(ticket, actor, "ACTUALIZAR", campo=nombre, antes=anterior,
                  despues=valor, motivo=motivo)
    if cambios_detalle:
        detalle.save()


def ejecutar(definicion, ticket, accion, actor, motivo="", datos=None):
    t = definicion.transicion(accion, ticket.estado)
    motivo = (motivo or "").strip()
    if t.requiere_motivo and not motivo:
        raise ValidationError("Esta acción exige un motivo.")
    datos = dict(datos or {})
    detalle = definicion.detalle_de(ticket)
    aplicar_campos(ticket, detalle, actor, datos, t.campos, motivo)
    contexto = Contexto(ticket, detalle, actor, datos, motivo, t)
    for guarda in t.guardas:
        guarda(contexto)
    if t.decision:
        Aprobacion = apps.get_model("processes", "Aprobacion")
        Aprobacion(
            ticket=ticket, aprobador=actor, decision=t.decision,
            estado_origen=ticket.estado, motivo=motivo, huella=detalle.huella(),
        ).save()
    anterior = ticket.estado
    ticket.estado = t.destino
    ahora = timezone.now()
    if t.destino in definicion.estados_resolucion and ticket.fecha_resolucion is None:
        ticket.fecha_resolucion = ahora
    if anterior in definicion.estados_resolucion and t.destino not in (
        definicion.estados_resolucion | definicion.finales
    ):
        ticket.fecha_resolucion = None  # Reapertura: el historial conserva la anterior.
    if t.destino in definicion.finales:
        ticket.fecha_cierre = ahora
        if ticket.fecha_resolucion is None:
            ticket.fecha_resolucion = ahora
    ticket.save()
    registrar(ticket, actor, accion.upper(), campo="estado", antes=anterior,
              despues=t.destino, motivo=motivo)
    for efecto in t.efectos:
        efecto(contexto)
    return ticket
