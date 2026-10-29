"""SD-P18 / PP2-P12: datos sintéticos, únicamente en la BD aislada del harness."""
import json
import os
import sys

import django

if os.environ.get("DB_NAME") != "catalogo_qa" or os.environ.get("DB_USER") != "catalogo_qa":
    raise SystemExit("P18 solo admite la base sintética catalogo_qa.")
django.setup()
from catalog.models import ServicioNivel1, ServicioNivel2
from cmdb.models import CI, RelacionCI
from organization.models import Empresa
from service_desk.models import AccionTicket, ComentarioTicket, Ticket

if len(sys.argv) != 2 or sys.argv[1] not in {"crear", "comprobar"}:
    raise SystemExit("Usa crear o comprobar.")
if sys.argv[1] == "crear":
    Empresa.objects.get_or_create(codigo="P12-PERSISTENCIA", defaults={
        "nombre": "Dato sintético conservado tras recrear contenedores",
    })
record = Empresa.objects.get(codigo="P12-PERSISTENCIA")
if record.nombre != "Dato sintético conservado tras recrear contenedores" or not record.estado:
    raise SystemExit("P18: dato controlado alterado.")
ultimo = Ticket.objects.order_by("pk").last()
resumen = {
    "P18": "dato_recuperado", "id": record.pk, "codigo": record.codigo, "nombre": record.nombre,
    "n1": ServicioNivel1.objects.count(), "n2": ServicioNivel2.objects.count(),
    "ci": CI.objects.count(), "relaciones_ci": RelacionCI.objects.count(),
    "tickets": Ticket.objects.count(), "bitacora": AccionTicket.objects.count(),
    "comentarios": ComentarioTicket.objects.count(),
    "ultimo_ticket": ultimo and [ultimo.numero, ultimo.estado, ultimo.acciones.count()],
}
if resumen["ci"] < 5000 or resumen["tickets"] < 35 or resumen["n2"] < 46:
    raise SystemExit(f"P18: faltan datos de catálogo/CMDB/tickets: {resumen}")
print(json.dumps(resumen, ensure_ascii=False, sort_keys=True))
