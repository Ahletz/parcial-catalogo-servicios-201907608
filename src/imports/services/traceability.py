"""Procedencia persistente separada de atributos editables."""

import re

from imports.models import IncidenciaImportacion, RegistroOrigen

from .normalizer import json_values


def coordinates(cells):
    positions = {position for cell in cells for position in (cell.coordinate, cell.principal)}
    return {
        "filas": sorted({int(re.search(r"\d+$", position).group()) for position in positions}),
        "celdas": sorted(positions),
        "rangos": sorted({cell.merged_range for cell in cells if cell.merged_range}),
    }


def snapshot(instance, fields):
    return json_values({name: getattr(instance, name) for name in fields})


def write_origin(execution, entry, instance, incoming, result, transformations):
    record = RegistroOrigen(
        ejecucion=execution, entidad=entry.entity,
        codigo=instance.codigo if entry.entity in {"NIVEL1", "NIVEL2"} else entry.code,
        hoja=execution.hoja, **coordinates(entry.cells),
        valores_originales={cell.coordinate: cell.evidence() for cell in entry.cells},
        valores_importados=json_values(incoming),
        valores_aplicados=snapshot(instance, incoming) | {"id": instance.pk},
        transformaciones=entry.transformations + transformations,
        revision_manual_capturada=instance.revision_manual,
        regla_aplicada="PD05/PD06/D14: selección de fuente y comparación por campo.",
        resultado=result,
    )
    if entry.entity == "NIVEL1":
        record.servicio_n1 = instance
    elif entry.entity == "NIVEL2":
        record.servicio_n2 = instance
    record.save(source="IMPORTACION")
    return record


def write_issue(execution, issue, record=None):
    incidence = IncidenciaImportacion(
        ejecucion=execution, registro=record, tipo=issue.kind,
        entidad=issue.entity, codigo=issue.code, hoja=execution.hoja,
        **coordinates(issue.cells), valores=issue.values,
        regla_aplicada=issue.rule, resultado=issue.result,
    )
    incidence.save(source="IMPORTACION")
    return incidence
