"""SD-P03/P16 sobre la BD aislada del harness con el conjunto real de 5,000 CI.

Genera dos veces (misma semilla), siembra la demo dos veces y mide filtros y
paginación por HTTP interno (django.test.Client). Solo admite catalogo_qa.
"""
import io
import json
import os
import platform
import time

import django

if os.environ.get("DB_NAME") != "catalogo_qa" or os.environ.get("DB_USER") != "catalogo_qa":
    raise SystemExit("El probe Service Desk solo admite catalogo_qa.")
django.setup()
from django.test.utils import setup_test_environment

# Sin esto Client no captura response.context fuera del test runner.
setup_test_environment()
from django.core.management import call_command
from django.db import connection
from django.test import Client

from accounts.models import Usuario
from cmdb.models import CI, ClasificacionCI
from service_desk.models import ColaServiceDesk, Ticket


def require(condition, message):
    if not condition:
        raise SystemExit(f"FALLO: {message}")


def run(command, **options):
    salida = io.StringIO()
    inicio = time.perf_counter()
    call_command(command, stdout=salida, **options)
    texto = salida.getvalue()
    return json.loads(texto[texto.index("{"):]), round(time.perf_counter() - inicio, 2)


gen1, t_gen1 = run("generate_cmdb", count=5000, seed=2026)
gen2, t_gen2 = run("generate_cmdb", count=5000, seed=2026)
require(gen2["total_conjunto"] >= 5000 and gen2["dispositivos_conjunto"] >= 5000, "Menos de 5,000.")
require(gen2["creados"] == 0 and gen2["relaciones_creadas"] == 0, "Segunda generación duplicó.")
require(CI.objects.filter(codigo__startswith="CI-2026-").values("codigo").distinct().count()
        == gen2["total_conjunto"], "Códigos repetidos.")
seed1, _ = run("seed_service_desk")
seed2, _ = run("seed_service_desk")
require(seed2["escenarios"] == 0 and seed2["tickets_demo"] == seed1["tickets_demo"],
        "Demo no idempotente.")
require(seed2["tickets_demo"] >= 35 and ColaServiceDesk.objects.count() >= 7, "Demo incompleta.")
require(all(n >= 5 for n in seed2["por_proceso"].values()), "Proceso con menos de 5 tickets.")

client = Client(HTTP_HOST="localhost")
client.force_login(Usuario.objects.get(identificador="consulta.demo"))
clase = ClasificacionCI.objects.get(codigo="HW-EST")
consultas = {
    "lista_pagina_1": "/cmdb/",
    "lista_pagina_100": "/cmdb/?page=100",
    "texto_codigo": "/cmdb/?q=CI-2026-049",
    "clasificacion_estado": f"/cmdb/?clasificacion={clase.pk}&estado=activo",
    "clasificacion_pagina_40": f"/cmdb/?clasificacion={clase.pk}&page=40",
    "responsable": "/cmdb/?responsable=admin.demo",
    "servicio": "/cmdb/?servicio=" + CI.objects.get(codigo="APP-2026-001")
    .vinculos_servicio.first().servicio.codigo,
    "grafo_impacto": "/cmdb/" + CI.objects.filter(clasificacion__codigo="HW-RED", estado=True)
    .order_by("codigo").first().codigo + "/grafo/?profundidad=4",
}
tiempos = {}
for nombre, url in consultas.items():
    inicio = time.perf_counter()
    respuesta = client.get(url)
    tiempos[nombre] = {"ms": round((time.perf_counter() - inicio) * 1000, 1),
                       "status": respuesta.status_code,
                       "total": getattr(respuesta.context.get("page"), "paginator", None)
                       and respuesta.context["page"].paginator.count}
    require(respuesta.status_code == 200, f"{url} devolvió {respuesta.status_code}")
require(tiempos["clasificacion_estado"]["total"] == CI.objects.filter(
    clasificacion=clase, estado=True).count(), "Filtro de clasificación incorrecto.")
require(tiempos["lista_pagina_1"]["total"] == CI.objects.count(), "Conteo de lista incorrecto.")
print(json.dumps({
    "P03": {"primera": gen1, "segunda": gen2, "segundos": [t_gen1, t_gen2]},
    "demo": {"primera": seed1, "segunda": seed2},
    "P16": tiempos,
    "entorno": {"python": platform.python_version(), "postgres": connection.pg_version,
                "plataforma": platform.platform(), "medicion": "django.test.Client en contenedor web"},
    "tickets": Ticket.objects.count(),
}, ensure_ascii=False, indent=2, default=str))
