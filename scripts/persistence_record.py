"""P12: dato sintético, únicamente en la BD aislada del harness."""
import json
import os
import sys

import django

if os.environ.get("DB_NAME") != "catalogo_qa" or os.environ.get("DB_USER") != "catalogo_qa":
    raise SystemExit("P12 solo admite la base sintética catalogo_qa.")
django.setup()
from catalog.models import ServicioNivel1, ServicioNivel2
from organization.models import Empresa

if len(sys.argv) != 2 or sys.argv[1] not in {"crear", "comprobar"}:
    raise SystemExit("Usa crear o comprobar.")
if sys.argv[1] == "crear":
    Empresa.objects.get_or_create(codigo="P12-PERSISTENCIA", defaults={
        "nombre": "Dato sintético conservado tras recrear contenedores",
    })
record = Empresa.objects.get(codigo="P12-PERSISTENCIA")
if record.nombre != "Dato sintético conservado tras recrear contenedores" or not record.estado:
    raise SystemExit("P12: dato controlado alterado.")
print(json.dumps({"P12": "dato_recuperado", "id": record.pk, "codigo": record.codigo,
                  "nombre": record.nombre, "n1": ServicioNivel1.objects.count(),
                  "n2": ServicioNivel2.objects.count()}, ensure_ascii=False, sort_keys=True))
