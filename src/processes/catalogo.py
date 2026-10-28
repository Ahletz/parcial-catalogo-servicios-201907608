"""Vocabulario ITSM compartido: procesos, tipos, categorías y niveles.

Sin importaciones de modelos para que Ticket, Cola y el motor lo reutilicen.
Las fuentes se citan en docs/PROCESOS.md; los valores marcados como decisión
del proyecto no son transcripciones literales de las diapositivas.
"""

from datetime import timedelta

from django.conf import settings
from django.db import models


class Proceso(models.TextChoices):
    NUEVOS_SERVICIOS = "NUEVOS_SERVICIOS", "Nuevos servicios"
    CAMBIOS = "CAMBIOS", "Cambios"
    INCIDENTES = "INCIDENTES", "Incidentes"
    EVENTOS = "EVENTOS", "Eventos"
    PROBLEMAS = "PROBLEMAS", "Problemas"
    ACCESOS = "ACCESOS", "Accesos"
    SERVICIOS_TECNOLOGIA = "SERVICIOS_TECNOLOGIA", "Servicios de tecnología"


class TipoTicket(models.TextChoices):
    """Seis tipos de L25-14."""

    SOLICITUD_ACCESO = "SOLICITUD_ACCESO", "Solicitud de acceso"
    EVENTO = "EVENTO", "Evento"
    INCIDENTE = "INCIDENTE", "Incidente"
    SOLICITUD_CAMBIO = "SOLICITUD_CAMBIO", "Solicitud de cambio"
    REQUISICION_SERVICIO = "REQUISICION_SERVICIO", "Requisición de servicio"
    PROBLEMA = "PROBLEMA", "Problema"


class SubtipoRequisicion(models.TextChoices):
    NUEVO_SERVICIO = "NUEVO_SERVICIO", "Nuevo servicio"
    SERVICIO_EXISTENTE = "SERVICIO_EXISTENTE", "Servicio existente"


# Mapeo explícito tipo (+subtipo) → proceso. Único punto de verdad.
MAPEO_TIPO_PROCESO = {
    (TipoTicket.SOLICITUD_ACCESO, ""): Proceso.ACCESOS,
    (TipoTicket.EVENTO, ""): Proceso.EVENTOS,
    (TipoTicket.INCIDENTE, ""): Proceso.INCIDENTES,
    (TipoTicket.SOLICITUD_CAMBIO, ""): Proceso.CAMBIOS,
    (TipoTicket.REQUISICION_SERVICIO, SubtipoRequisicion.NUEVO_SERVICIO):
        Proceso.NUEVOS_SERVICIOS,
    (TipoTicket.REQUISICION_SERVICIO, SubtipoRequisicion.SERVICIO_EXISTENTE):
        Proceso.SERVICIOS_TECNOLOGIA,
    (TipoTicket.PROBLEMA, ""): Proceso.PROBLEMAS,
}


def proceso_de(tipo, subtipo=""):
    return MAPEO_TIPO_PROCESO.get((tipo, subtipo or ""))


class Prioridad(models.IntegerChoices):
    """Menor valor = se atiende antes (orden de cola determinista)."""

    CRITICA = 1, "Crítica"
    ALTA = 2, "Alta"
    MEDIA = 3, "Media"
    BAJA = 4, "Baja"


class Nivel(models.TextChoices):
    ALTO = "ALTO", "Alto"
    MEDIO = "MEDIO", "Medio"
    BAJO = "BAJO", "Bajo"


class Canal(models.TextChoices):
    PORTAL = "PORTAL", "Portal"
    CORREO = "CORREO", "Correo"
    TELEFONO = "TELEFONO", "Teléfono"
    PRESENCIAL = "PRESENCIAL", "Presencial"
    MONITOREO = "MONITOREO", "Monitoreo"


class NivelSoporte(models.IntegerChoices):
    """Numeración canónica L25-11 (0–4)."""

    AUTOSERVICIO = 0, "0 — Autoservicio"
    HELP_DESK = 1, "1 — Help Desk"
    SOPORTE_TECNICO = 2, "2 — Soporte técnico"
    INGENIEROS = 3, "3 — Ingenieros"
    EXTERNO = 4, "4 — Externo / proveedores"


# L25-12/13 numeran 0–3. Equivalencia documentada; sin cuotas 20/70/5/5.
EQUIVALENCIA_SOPORTE_0_3 = {
    NivelSoporte.AUTOSERVICIO: 0,
    NivelSoporte.HELP_DESK: 1,
    NivelSoporte.SOPORTE_TECNICO: 2,
    NivelSoporte.INGENIEROS: 2,
    NivelSoporte.EXTERNO: 3,
}


class CategoriaEvento(models.TextChoices):
    E0 = "E0", "E0 — Programado: solo registro"
    E1 = "E1", "E1 — Sin impacto: registro y evaluación"
    E2 = "E2", "E2 — Impacto al servicio: incidente"
    E3 = "E3", "E3 — Impacto de seguridad: incidente"


EVENTOS_CON_INCIDENTE = {CategoriaEvento.E2, CategoriaEvento.E3}


class CategoriaIncidente(models.TextChoices):
    I0 = "I0", "I0 — No causa interrupción"
    I1 = "I1", "I1 — 3 horas o menos (incluye degradación)"
    I2 = "I2", "I2 — 8 horas o menos (incluye degradación)"
    I3 = "I3", "I3 — 2 días o menos"
    I4 = "I4", "I4 — 1 semana o menos"
    I5 = "I5", "I5 — 1 mes o más"
    I6 = "I6", "I6 — Afecta seguridad de recursos/información"


# Tabla L25-16 transcrita: referencia docente, no SLA ni valor operativo.
REFERENCIA_INCIDENTES = {
    CategoriaIncidente.I0: {"prioridad": "BAJA", "redundancia": True},
    CategoriaIncidente.I1: {"prioridad": "MEDIA", "redundancia": False},
    CategoriaIncidente.I2: {"prioridad": "MEDIA", "redundancia": False},
    CategoriaIncidente.I3: {"prioridad": "ALTA", "redundancia": False},
    CategoriaIncidente.I4: {"prioridad": "ALTA", "redundancia": False},
    CategoriaIncidente.I5: {"prioridad": "ALTA", "redundancia": False},
    CategoriaIncidente.I6: {"prioridad": "ALTA", "redundancia": False},
}


class Afectacion(models.TextChoices):
    SIN_INTERRUPCION = "SIN_INTERRUPCION", "Sin interrupción"
    DEGRADACION = "DEGRADACION", "Degradación"
    INTERRUPCION = "INTERRUPCION", "Interrupción"
    SEGURIDAD = "SEGURIDAD", "Seguridad"


# Regla complementaria (decisión SD-DP05): bandas consecutivas y excluyentes
# sobre los rótulos de L25-16. El hueco (1 semana, 1 mes) queda sin sugerencia.
# Configurable con settings.SD_BANDAS_INCIDENTE: [(categoria, desde, hasta)].
BANDAS_INCIDENTE = [
    (CategoriaIncidente.I1, timedelta(0), timedelta(hours=3)),
    (CategoriaIncidente.I2, timedelta(hours=3), timedelta(hours=8)),
    (CategoriaIncidente.I3, timedelta(hours=8), timedelta(days=2)),
    (CategoriaIncidente.I4, timedelta(days=2), timedelta(weeks=1)),
    (CategoriaIncidente.I5, timedelta(days=30), None),
]


def sugerir_categoria_incidente(afectacion, duracion):
    """Devuelve una categoría sugerida o None; nunca la asigna por sí misma.

    Límite inferior exclusivo y superior inclusivo (I1 incluye 3 h exactas).
    I5 empieza en 30 días: «1 mes» se fija en 30 días como decisión del proyecto.
    """
    if afectacion == Afectacion.SEGURIDAD:
        return CategoriaIncidente.I6
    if afectacion == Afectacion.SIN_INTERRUPCION:
        return CategoriaIncidente.I0
    if duracion is None or duracion <= timedelta(0):
        return None
    for categoria, desde, hasta in getattr(settings, "SD_BANDAS_INCIDENTE", BANDAS_INCIDENTE):
        if categoria == CategoriaIncidente.I5 and duracion >= desde:
            return categoria
        if duracion > desde and hasta is not None and duracion <= hasta:
            return categoria
    return None
