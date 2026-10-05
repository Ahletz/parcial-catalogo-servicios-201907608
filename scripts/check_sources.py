"""Integridad de fuentes originales, sin abrir celdas ni importar registros."""

from hashlib import sha256
from pathlib import Path

EXPECTED = {
    "ENUNCIADO.md": "c99201ed3e60aadbed9c7bebbfcc970290e6d13287eec0cbac984d01a0d55cfa",
    "CatalogoServicios.xlsx": "de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0",
}

for name, expected in EXPECTED.items():
    if sha256((Path("/fuentes") / name).read_bytes()).hexdigest() != expected:
        raise SystemExit(f"Fuente original alterada: {name}")
    print(f"{name}: integridad verificada.")
