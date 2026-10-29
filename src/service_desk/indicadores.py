"""Indicadores calculados desde tickets y bitácora; tiempo calendario.

- Antigüedad: abiertos = corte − creación; cerrados = cierre − creación.
- Primera atención: primera AccionTicket de alguien distinto del solicitante
  que no sea administrativa (crear, tomar, asignar, transferir, vincular,
  adjuntar, reclasificar) menos la creación. Sin atención: «pendiente», no cero.
- Resolución: fecha_resolucion − creación (ciclo vigente: reabrir limpia
  fecha_resolucion, y la nueva resolución se mide desde la apertura original).
- Pausas: no existen en el modelo; no se descuentan intervalos.
- Cumplimiento: resueltos con objetivo de su cola y tiempo ≤ objetivo /
  resueltos con objetivo. Denominador 0 → «sin datos». Abiertos que ya
  superaron el objetivo se cuentan aparte como vencidos.
"""

from collections import Counter, defaultdict

from django.utils import timezone

from .models import AccionTicket

NO_ATENCION = {"CREAR", "VINCULAR_CI", "TOMAR", "ASIGNAR", "REASIGNAR", "LIBERAR",
               "TRANSFERIR", "RECLASIFICAR", "ADJUNTAR", "RELACIONAR", "VINCULAR_INCIDENTE"}


def horas(delta):
    return round(delta.total_seconds() / 3600, 2)


def resumen(valores):
    if not valores:
        return {"n": 0, "promedio_h": None, "maximo_h": None}
    return {"n": len(valores), "promedio_h": horas(sum(valores, start=valores[0] * 0) / len(valores)),
            "maximo_h": horas(max(valores))}


def primeras_atenciones(tickets):
    ids = {t.pk: t for t in tickets}
    primeras = {}
    acciones = AccionTicket.objects.filter(ticket_id__in=ids).exclude(
        accion__in=NO_ATENCION).order_by("pk").values_list("ticket_id", "actor_id", "created_at")
    for ticket_id, actor_id, fecha in acciones:
        if ticket_id not in primeras and actor_id != ids[ticket_id].solicitante_id:
            primeras[ticket_id] = fecha
    return primeras


def calcular(tickets, corte=None):
    corte = corte or timezone.now()
    tickets = list(tickets.select_related("cola"))
    primeras = primeras_atenciones(tickets)
    conteos = {nombre: Counter() for nombre in ("cola", "proceso", "prioridad", "estado")}
    antig_abiertos, antig_cerrados, atencion, resolucion = [], [], [], []
    cumplimiento = defaultdict(lambda: {"elegibles": 0, "cumplidos": 0, "vencidos_abiertos": 0,
                                        "atencion_elegibles": 0, "atencion_cumplidos": 0})
    sin_atencion = 0
    for t in tickets:
        conteos["cola"][t.cola.codigo] += 1
        conteos["proceso"][t.get_proceso_display()] += 1
        conteos["prioridad"][t.get_prioridad_display()] += 1
        conteos["estado"][t.estado] += 1
        if t.fecha_cierre:
            antig_cerrados.append(t.fecha_cierre - t.created_at)
        else:
            antig_abiertos.append(corte - t.created_at)
        primera = primeras.get(t.pk)
        if primera:
            atencion.append(primera - t.created_at)
        else:
            sin_atencion += 1
        fila = cumplimiento[t.cola.codigo]
        objetivo_atencion = t.cola.objetivo_primera_atencion
        if objetivo_atencion and primera:
            fila["atencion_elegibles"] += 1
            fila["atencion_cumplidos"] += int(primera - t.created_at <= objetivo_atencion)
        objetivo = t.cola.objetivo_resolucion
        if t.fecha_resolucion:
            duracion = t.fecha_resolucion - t.created_at
            resolucion.append(duracion)
            if objetivo:
                fila["elegibles"] += 1
                fila["cumplidos"] += int(duracion <= objetivo)
        elif objetivo and corte - t.created_at > objetivo:
            fila["vencidos_abiertos"] += 1
    for fila in cumplimiento.values():
        fila["porcentaje"] = (round(100 * fila["cumplidos"] / fila["elegibles"], 1)
                              if fila["elegibles"] else None)
        fila["porcentaje_atencion"] = (
            round(100 * fila["atencion_cumplidos"] / fila["atencion_elegibles"], 1)
            if fila["atencion_elegibles"] else None)
    return {
        "corte": corte, "total": len(tickets),
        "abiertos": len(antig_abiertos), "cerrados": len(antig_cerrados),
        "conteos": {k: sorted(v.items()) for k, v in conteos.items()},
        "antiguedad_abiertos": resumen(antig_abiertos),
        "antiguedad_cerrados": resumen(antig_cerrados),
        "primera_atencion": resumen(atencion), "sin_primera_atencion": sin_atencion,
        "resolucion": resumen(resolucion),
        "cumplimiento": dict(sorted(cumplimiento.items())),
    }
