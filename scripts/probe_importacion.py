"""Dos invocaciones CLI reales en una BD test_ nueva, nunca sobre la normal."""

import json
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql

SOURCE = Path("/app/data/CatalogoServicios.xlsx")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def command(*arguments):
    process = subprocess.run(
        [sys.executable, "manage.py", *arguments],
        capture_output=True, text=True, check=False,
    )
    require(process.returncode == 0, f"Comando {arguments[0]} falló: {process.stderr}")
    return process


def main():
    require(
        os.environ.get("DB_NAME") == "catalogo_modelos"
        and os.environ.get("DB_HOST") == "db"
        and os.environ.get("DB_USER") == "modelos",
        "La demostración solo se ejecuta en el Compose interno autorizado.",
    )
    database = "test_importacion_evidencia_" + uuid4().hex
    require(len(database) <= 63 and database.startswith("test_"), "Nombre de BD inválido.")
    with psycopg.connect(
        dbname="postgres", host="db", user="modelos", autocommit=True
    ) as administration:
        with administration.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    os.environ["DB_NAME"] = database
    os.environ["DB_TEST_NAME"] = "test_no_usar_" + uuid4().hex
    import django

    django.setup()
    from catalog.models import (
        ClaseServicio, CriticidadServicio, ServicioNivel1, ServicioNivel2, TipoServicio,
    )
    from imports.models import EjecucionImportacion, IncidenciaImportacion, RegistroOrigen

    before = sha256(SOURCE.read_bytes()).hexdigest()
    migration = command("migrate", "--noinput")
    reports = []
    return_codes = []
    for _ in range(2):
        process = command("import_catalog", "--file", str(SOURCE))
        return_codes.append(process.returncode)
        heading, _, content = process.stdout.partition("\n")
        require(heading == "Importación completada", "Salida CLI inesperada.")
        reports.append(json.loads(content))
        require(
            ServicioNivel1.objects.count() == 12 and ServicioNivel2.objects.count() == 46,
            "Cardinalidades 12/46 incorrectas.",
        )
        require(
            ClaseServicio.objects.count() == 2 and CriticidadServicio.objects.count() == 5
            and TipoServicio.objects.count() == 11,
            "Catálogos incompletos o duplicados.",
        )
    require(reports[0]["totales"]["creados"] == 76, "Primera importación incompleta.")
    require(reports[1]["totales"] == {
        "creados": 0, "actualizados": 0, "omitidos": 76, "observados": 4,
    }, "Segunda importación no idempotente.")
    persisted = {
        "ejecuciones": EjecucionImportacion.objects.filter(estado="COMPLETADA").count(),
        "origenes": RegistroOrigen.objects.count(),
        "incidencias": IncidenciaImportacion.objects.count(),
    }
    require(persisted == {
        "ejecuciones": 2, "origenes": 152, "incidencias": 8,
    }, "Trazabilidad incompleta.")
    after = sha256(SOURCE.read_bytes()).hexdigest()
    require(before == after, "Excel original alterado.")
    print(json.dumps({
        "base_pruebas_conservada": database,
        "comando_migraciones": "python manage.py migrate --noinput",
        "codigo_migraciones": migration.returncode,
        "comando_importacion": (
            "python manage.py import_catalog --file /app/data/CatalogoServicios.xlsx"
        ),
        "codigos_importaciones": return_codes,
        "primera": reports[0], "segunda": reports[1],
        "persistido": persisted,
        "sha256_antes": before, "sha256_despues": after,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
