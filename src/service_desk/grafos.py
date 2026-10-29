"""Grafo 2 — trazabilidad ITSM: cadena evento → incidente → problema → cambio.

Nodos: Ticket. Aristas: RelacionTicket (dirigidas origen → destino) y el
vínculo DetalleEvento.incidente, que se materializa también como relación
EVENTO_INCIDENTE. El recorrido sigue ambas direcciones para reconstruir la
cadena completa desde cualquier punto; BFS con visitados y profundidad máxima.
Solo incluye tickets que el usuario puede ver; los demás quedan como «oculto».
"""

from collections import deque

from .models import RelacionTicket, Ticket
from .permisos import puede_ver

PROFUNDIDAD_MAXIMA = 6
ORDEN_PROCESO = {"EVENTOS": 0, "INCIDENTES": 1, "PROBLEMAS": 2, "CAMBIOS": 3}


def cadena(usuario, ticket, profundidad=4):
    try:
        profundidad = max(1, min(int(profundidad), PROFUNDIDAD_MAXIMA))
    except (TypeError, ValueError):
        profundidad = 4
    niveles = {ticket.pk: 0}
    aristas = set()
    cola = deque([ticket.pk])
    while cola:
        actual = cola.popleft()
        if niveles[actual] >= profundidad:
            continue
        relaciones = RelacionTicket.objects.filter(origen_id=actual) | RelacionTicket.objects.filter(
            destino_id=actual
        )
        for origen, destino, tipo in relaciones.values_list("origen_id", "destino_id", "tipo"):
            aristas.add((origen, destino, tipo))
            vecino = destino if origen == actual else origen
            if vecino not in niveles:
                niveles[vecino] = niveles[actual] + 1
                cola.append(vecino)
    tickets = Ticket.objects.filter(pk__in=niveles).select_related("cola")
    visibles = {t.pk: t for t in tickets if puede_ver(usuario, t)}
    nodos = sorted(
        visibles.values(), key=lambda t: (ORDEN_PROCESO.get(t.proceso, 9), t.created_at)
    )
    return {
        "raiz": ticket, "nodos": nodos, "ocultos": len(niveles) - len(visibles),
        "aristas": sorted(
            (a for a in aristas if a[0] in visibles and a[1] in visibles), key=lambda a: a[:2]
        ),
        "visibles": visibles,
    }
