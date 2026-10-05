from contextlib import contextmanager
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from openpyxl import load_workbook

ORIGINAL = Path(__file__).resolve().parents[1] / "data" / "CatalogoServicios.xlsx"
CLASSES = {"A DEMANDA", "RECURRENTE"}
CRITICALITIES = {"Very Low", "Low", "Normal", "High", "Very High"}
TYPES = {
    "Back End", "Demostration", "End User Service", "Front End", "IT Management",
    "IT Operational", "Other", "Project", "Reporting", "Training", "Underpinning Contract",
}


@contextmanager
def changed_source(change):
    """Solo copias nuevas en tmp; jamás guardar sobre ORIGINAL."""
    with TemporaryDirectory(prefix="catalogo-import-test-") as directory:
        book = load_workbook(BytesIO(ORIGINAL.read_bytes()), keep_links=False)
        try:
            change(book)
            target = Path(directory) / "fuente-pruebas.xlsx"
            book.save(target)
        finally:
            book.close()
        yield target


def command_report(file=ORIGINAL):
    import json

    output = StringIO()
    call_command("import_catalog", file=str(file), stdout=output)
    heading, _, data = output.getvalue().partition("\n")
    if heading != "Importación completada":
        raise AssertionError(output.getvalue())
    return json.loads(data)
