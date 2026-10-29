"""Grafo 1 — CMDB: recorrido de impacto potencial sobre RelacionCI.

Nodos: CI. Aristas: RelacionCI activas. Dirección de impacto: en tipos
dirigidos «A depende_de/alojado_en B», si B falla A queda potencialmente
afectado, así que el recorrido sigue aristas ENTRANTES (destino → origen).
Tipos no dirigidos (conectado_a) se muestran como vecinos pero no propagan
impacto. BFS con conjunto de visitados (ciclos permitidos no generan bucles),
profundidad máxima y tope de nodos. «Potencialmente afectado» nunca significa
interrupción confirmada.
"""

from collections import deque

from .models import CI, RelacionCI, ServicioCI

PROFUNDIDAD_MAXIMA = 6
NODOS_MAXIMOS = 200


def impacto(ci, profundidad=3, limite=NODOS_MAXIMOS):
    try:
        profundidad = max(1, min(int(profundidad), PROFUNDIDAD_MAXIMA))
    except (TypeError, ValueError):
        profundidad = 3
    niveles = {ci.pk: 0}
    aristas, cortado = [], False
    cola = deque([ci.pk])
    while cola:
        actual = cola.popleft()
        if niveles[actual] >= profundidad:
            continue
        entrantes = RelacionCI.objects.filter(
            destino_id=actual, estado=True, tipo__dirigida=True
        ).values_list("origen_id", "tipo__nombre")
        for origen, tipo in entrantes:
            aristas.append((origen, actual, tipo))
            if origen in niveles:
                continue  # Ya visitado: corta ciclos.
            if len(niveles) >= limite:
                cortado = True
                continue
            niveles[origen] = niveles[actual] + 1
            cola.append(origen)
    nodos = {c.pk: c for c in CI.objects.filter(pk__in=niveles).select_related("clasificacion")}
    servicios = {}
    for vinculo in ServicioCI.objects.filter(ci_id__in=niveles, estado=True).select_related(
        "servicio"
    ):
        servicios.setdefault(vinculo.servicio, set()).add(vinculo.ci_id)
    vecinos = list(RelacionCI.objects.filter(estado=True, tipo__dirigida=False).filter(
        origen_id=ci.pk).values_list("destino_id", flat=True)) + list(
        RelacionCI.objects.filter(estado=True, tipo__dirigida=False, destino_id=ci.pk)
        .values_list("origen_id", flat=True))
    dependencias = list(RelacionCI.objects.filter(
        origen_id=ci.pk, estado=True, tipo__dirigida=True
    ).select_related("destino", "tipo"))
    return {
        "raiz": ci, "profundidad": profundidad, "cortado": cortado,
        "nodos": [(nodos[pk], nivel) for pk, nivel in sorted(niveles.items(), key=lambda x: x[1])],
        "aristas": aristas, "dependencias": dependencias,
        "conectados": list(CI.objects.filter(pk__in=vecinos)),
        "servicios": sorted(
            ((s, len(cis)) for s, cis in servicios.items()), key=lambda x: x[0].codigo
        ),
    }


def disposicion(columnas, ancho_columna=230, alto_fila=46):
    """Coordenadas SVG por columnas: {clave: (x, y)} y tamaño del lienzo."""
    posiciones, filas = {}, {}
    for clave, columna in columnas:
        fila = filas.get(columna, 0)
        filas[columna] = fila + 1
        posiciones[clave] = (40 + columna * ancho_columna, 30 + fila * alto_fila)
    ancho = 40 + (max(filas) + 1 if filas else 1) * ancho_columna
    alto = 30 + (max(filas.values()) if filas else 1) * alto_fila
    return posiciones, ancho, alto
