"""Reglas de datos puras: selección determinista, NULL y casos del original."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from .exceptions import CatalogImportError
from .parser import ORIGINAL_SHA256, CellData, ParsedWorkbook, empty


@dataclass
class Issue:
    kind: str
    entity: str
    code: str
    cells: list[CellData]
    values: dict
    rule: str
    result: dict


@dataclass
class Entry:
    entity: str
    code: str
    values: dict
    cells: list[CellData]
    transformations: list[dict] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


@dataclass
class ImportPlan:
    workbook: ParsedWorkbook
    levels1: list[Entry]
    levels2: list[Entry]
    catalogs: dict[str, list[Entry]]
    orphan_issues: list[Issue]
    continuations: int
    empty_rows: int
    active_options: dict


def text(value, coordinate, required=False):
    if empty(value):
        if required:
            raise CatalogImportError(f"Valor obligatorio ausente: {coordinate}.")
        return None
    if not isinstance(value, str) or not value.strip():
        raise CatalogImportError(f"Se requiere texto original válido: {coordinate}.")
    return value  # No strip, casefold ni correcciones silenciosas.


def active(value, coordinate):
    if empty(value):
        return None
    if value not in {"S", "N"}:
        raise CatalogImportError(f"ACTIVO debe ser S, N o ausente: {coordinate}.")
    return value == "S"


def number(value, coordinate):
    if empty(value):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise CatalogImportError(f"Umbral numérico inválido: {coordinate}.")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise CatalogImportError(f"Umbral numérico inválido: {coordinate}.") from exc
    if not result.is_finite():
        raise CatalogImportError(f"Umbral no finito: {coordinate}.")
    return result


def decimal_text(value):
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return "0" if result in {"-0", ""} else result


def json_values(values):
    return {
        key: decimal_text(value) if isinstance(value, Decimal) else value
        for key, value in values.items()
    }


def choose(cells, entity, code, column, issues):
    candidates = [cell for cell in cells if cell.column == column and not empty(cell.value)]
    if not candidates:
        return None
    first = candidates[0]
    if entity == "NIVEL1" and code == "SE.12" and column == "B":
        first = next(
            (cell for cell in candidates if cell.value == "Suministrar Analitica"),
            first,
        )
    distinct = []
    for cell in candidates:
        if cell.value not in distinct:
            distinct.append(cell.value)
    if len(distinct) > 1:
        issues.append(Issue(
            kind=f"CONFLICTO_{'N1' if entity == 'NIVEL1' else 'N2'}",
            entity=entity, code=code, cells=candidates,
            values={
                "columna": column,
                "candidatos": [
                    {"celda": cell.coordinate, "principal": cell.principal, "valor": cell.value}
                    for cell in candidates
                ],
            },
            rule=(
                "SE.12: canónico presente Suministrar Analitica."
                if entity == "NIVEL1" and code == "SE.12" and column == "B"
                and first.value == "Suministrar Analitica"
                else "Principal/primera no vacía dentro de la identidad autorizada."
            ),
            result={"valor_elegido": first.value, "principal": first.principal},
        ))
    return first.value


def merge_transformations(cells):
    used = {}
    for cell in cells:
        if cell.merged_range:
            used[cell.merged_range] = {
                "regla": "PRINCIPAL_DENTRO_DEL_RANGO",
                "rango": cell.merged_range, "principal": cell.principal,
            }
    return list(used.values())


def prepare(workbook):
    n1_rows = {}
    n2_rows = {}
    orphan_issues = []
    for row in workbook.rows:
        code1 = text(row.cells["A"].value, f"A{row.number}")
        if code1 is not None:
            n1_rows.setdefault(code1, []).append(row)
        if row.kind in {"SERVICIO", "CONTINUACION"}:
            code2 = text(row.cells["C"].value, f"C{row.number}", required=True)
            n2_rows.setdefault(code2, []).append(row)
        elif row.kind == "OBSERVADA":
            cells = list(row.cells.values())
            orphan_issues.append(Issue(
                "FILA_SIN_IDENTIDAD", "", "", cells,
                {"originales": {cell.coordinate: cell.evidence() for cell in cells}},
                "Sin C explícita ni combinación C: no asociar a un vecino.",
                {"accion": "OBSERVADA_SIN_CREAR_NI_ASIGNAR_SERVICIO"},
            ))
    levels1 = []
    for code, rows in n1_rows.items():
        cells = [row.cells[col] for row in rows for col in ("A", "B")]
        issues = []
        name = text(choose(cells, "NIVEL1", code, "B", issues), "B", required=True)
        levels1.append(Entry(
            "NIVEL1", code, {"codigo": code, "nombre": name}, cells,
            merge_transformations(cells), issues,
        ))
    if not levels1 or not n2_rows:
        raise CatalogImportError("No hay identidades N1/N2 importables en las filas 5–101.")
    catalogs = {}
    for entity, column in (("CLASE", "F"), ("CRITICIDAD", "G"), ("TIPO", "H")):
        groups = {}
        for cell in workbook.options[column]:
            label = text(cell.value, cell.coordinate)
            if label is not None:
                groups.setdefault(label, []).append(cell)
        if not groups:
            raise CatalogImportError(f"Lista de opciones vacía: {column}112:{column}122.")
        catalogs[entity] = [
            Entry(entity, label, {"etiqueta": label}, cells, merge_transformations(cells))
            for label, cells in groups.items()
        ]
    active_options = {}
    for cell in workbook.options["E"]:
        if not empty(cell.value):
            active_options[cell.value] = {
                "celda": cell.coordinate, "valor": cell.value,
                "interpretado": active(cell.value, cell.coordinate),
            }
    if set(active_options) != {"S", "N"}:
        raise CatalogImportError("Opciones ACTIVO E112:E122 deben definir S y N.")
    levels2 = []
    for code, rows in n2_rows.items():
        cells = [cell for row in rows for cell in row.cells.values()]
        issues = []
        parent = choose(cells, "NIVEL2", code, "A", issues)
        transformations = merge_transformations(cells)
        if empty(parent):
            matches = [candidate for candidate in n1_rows if code.startswith(candidate + ".")]
            if len(matches) != 1:
                raise CatalogImportError(
                    f"N2 sin N1 explícito y sin prefijo exacto único: C{rows[0].number}."
                )
            parent = matches[0]
            inference = {
                "regla": "PREFIJO_EXACTO_Y_UNICO", "codigo_fuente": code,
                "padre_inferido": parent, "celdas": [f"C{rows[0].number}"],
            }
            transformations.append(inference)
            issues.append(Issue(
                "INFERENCIA_N1", "NIVEL2", code, list(rows[0].cells.values()),
                {"A_original": rows[0].cells["A"].raw, "codigo_n2": code},
                "Prefijo N1 + punto exacto y único; sin copiar fila anterior.", inference,
            ))
        if parent not in n1_rows:
            raise CatalogImportError(f"Padre N1 de fuente inexistente: C{rows[0].number}.")
        values = {"codigo": code, "nivel1_codigo": parent}
        for attribute, column in (
            ("nombre", "D"), ("activo", "E"), ("clase", "F"),
            ("criticidad", "G"), ("tipo", "H"), ("descripcion", "I"),
            ("metrica", "J"), ("minimo", "K"), ("maximo", "L"),
        ):
            value = choose(cells, "NIVEL2", code, column, issues)
            if attribute == "activo":
                value = active(value, f"E{rows[0].number}")
            elif attribute in {"minimo", "maximo"}:
                value = number(value, f"{column}{rows[0].number}")
            else:
                value = text(value, f"{column}{rows[0].number}", required=attribute == "nombre")
            if attribute in {"clase", "criticidad", "tipo"} and value is not None:
                entity = {"clase": "CLASE", "criticidad": "CRITICIDAD", "tipo": "TIPO"}[attribute]
                if value not in {item.code for item in catalogs[entity]}:
                    raise CatalogImportError(
                        f"Etiqueta fuera de opciones controladas: {column}{rows[0].number}."
                    )
            values[attribute] = value
        if values["minimo"] is not None and values["maximo"] is not None:
            if values["minimo"] > values["maximo"]:
                raise CatalogImportError(f"Mínimo mayor que máximo: K{rows[0].number}.")
        transformations.append({
            "regla": "ACTIVO_S_N_NULL", "opciones_origen": active_options,
            "valor_interpretado": values["activo"],
        })
        levels2.append(Entry("NIVEL2", code, values, cells, transformations, issues))
    if workbook.source.digest == ORIGINAL_SHA256 and (
        len(levels1) != 12 or len(levels2) != 46
    ):
        raise CatalogImportError("El original no produjo las cardinalidades de control 12/46.")
    return ImportPlan(
        workbook, levels1, levels2, catalogs, orphan_issues,
        sum(row.kind == "CONTINUACION" for row in workbook.rows),
        sum(row.kind == "VACIA" for row in workbook.rows), active_options,
    )
