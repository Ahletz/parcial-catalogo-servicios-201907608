import json

from django.core.management.base import BaseCommand, CommandError

from imports.services.exceptions import CatalogImportError
from imports.services.importer import import_catalog


class Command(BaseCommand):
    help = "Importa el catálogo Excel con procedencia, atomicidad e idempotencia."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Ruta del XLSX de solo lectura.")

    def handle(self, *args, **options):
        try:
            result = import_catalog(options["file"])
        except CatalogImportError as exc:
            identifier = f" (ejecución {exc.execution_id})" if exc.execution_id else ""
            raise CommandError(f"Importación fallida{identifier}: {exc}") from exc
        self.stdout.write("Importación completada")
        self.stdout.write(json.dumps(result.report(), ensure_ascii=False, indent=2))
