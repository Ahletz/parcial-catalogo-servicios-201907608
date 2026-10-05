"""Transacción funcional, reconciliación y reporte de cada ejecución."""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.utils import timezone

from catalog.models import (
    ClaseServicio, CriticidadServicio, ServicioNivel1, ServicioNivel2, TipoServicio,
)
from config.domain import domain_transaction
from imports.models import EjecucionImportacion, RegistroOrigen

from .exceptions import CatalogImportError
from .normalizer import Issue, json_values, prepare
from .parser import SHEET_NAME, parse_workbook, read_source
from .traceability import snapshot, write_issue, write_origin

MODELS = {
    "CLASE": ClaseServicio, "CRITICIDAD": CriticidadServicio, "TIPO": TipoServicio,
    "NIVEL1": ServicioNivel1, "NIVEL2": ServicioNivel2,
}
ACTIONS = {"CREADO": "creados", "ACTUALIZADO": "actualizados", "OMITIDO": "omitidos"}


@dataclass(frozen=True)
class ImportResult:
    execution: EjecucionImportacion

    def report(self):
        return {
            "ejecucion": self.execution.pk, "archivo": self.execution.archivo,
            "sha256": self.execution.sha256, "hoja": self.execution.hoja,
            "estado": self.execution.estado,
            "totales": {
                name: getattr(self.execution, name)
                for name in ("creados", "actualizados", "omitidos", "observados")
            },
            "detalle": self.execution.contadores_por_entidad,
        }


def origin_for_target(entry, instance):
    records = RegistroOrigen.objects.filter(
        entidad=entry.entity, ejecucion__estado="COMPLETADA"
    )
    if entry.entity == "NIVEL1":
        records = records.filter(servicio_n1=instance)
    elif entry.entity == "NIVEL2":
        records = records.filter(servicio_n2=instance)
    else:
        records = records.filter(valores_aplicados__id=instance.pk)
    return records.order_by("-pk").first()


def find_target(entry):
    model = MODELS[entry.entity]
    key = "codigo" if entry.entity in {"NIVEL1", "NIVEL2"} else "etiqueta"
    source_origin = RegistroOrigen.objects.filter(
        entidad=entry.entity, ejecucion__estado="COMPLETADA",
        **{f"valores_importados__{key}": entry.code},
    ).order_by("-pk").first()
    instance = None
    if source_origin:
        instance = model.objects.filter(
            pk=source_origin.valores_aplicados.get("id")
        ).first()
    if instance is None:
        instance = model.objects.filter(**{key: entry.code}).first()
    return instance


def persist_entry(execution, entry, incoming):
    instance = find_target(entry)
    issues = list(entry.issues)
    transformations = []
    if instance is None:
        attributes = dict(incoming)
        if entry.entity == "NIVEL2":
            attributes["origen"] = "IMPORTADO"
        instance = MODELS[entry.entity](**attributes)
        instance.save(source="IMPORTACION")
        result = "CREADO"
    else:
        previous = origin_for_target(entry, instance)
        baseline = previous.valores_importados if previous else {}
        current = snapshot(instance, incoming)
        new = json_values(incoming)
        changed = []
        for name, value in new.items():
            if current[name] == value:
                continue
            if previous and name in baseline and current[name] == baseline[name]:
                setattr(instance, name, incoming[name])
                changed.append(name)
            else:
                issues.append(Issue(
                    "DIVERGENCIA_HUMANA" if previous else "COLISION_SIN_PROCEDENCIA",
                    entry.entity, entry.code, entry.cells,
                    {
                        "campo": name, "previo_importado": baseline.get(name),
                        "actual": current[name], "nuevo_excel": value,
                        "revision_manual": instance.revision_manual,
                        "revision_previa": (
                            previous.revision_manual_capturada if previous else None
                        ),
                    },
                    "D14/PD06: conservar actual divergente; baseline importado, no aplicado.",
                    {"accion": "CONSERVADO_PARA_REVISION", "campo": name},
                ))
        if changed:
            instance.save(source="IMPORTACION")
        result = "ACTUALIZADO" if changed else "OMITIDO"
        transformations.append({
            "regla": "COMPARACION_TRES_VALORES_POR_CAMPO",
            "origen_previo_id": previous.pk if previous else None,
            "campos_actualizados": changed,
            "campos_conservados": [
                issue.values["campo"] for issue in issues
                if issue.kind in {"DIVERGENCIA_HUMANA", "COLISION_SIN_PROCEDENCIA"}
            ],
        })
    record = write_origin(execution, entry, instance, incoming, result, transformations)
    for issue in issues:
        write_issue(execution, issue, record)
    return instance, result, bool(issues), len(issues)


def functional_import(execution, plan):
    counts = {
        entity: {"creados": 0, "actualizados": 0, "omitidos": 0, "observados": 0}
        for entity in MODELS
    }
    targets = {entity: {} for entity in MODELS}
    incidences = 0

    def process(entry, incoming):
        nonlocal incidences
        instance, result, observed, issue_count = persist_entry(execution, entry, incoming)
        if any(target.pk == instance.pk for target in targets[entry.entity].values()):
            raise CatalogImportError("Dos identidades de fuente apuntan a una entidad funcional.")
        targets[entry.entity][entry.code] = instance
        counts[entry.entity][ACTIONS[result]] += 1
        counts[entry.entity]["observados"] += int(observed)
        incidences += issue_count

    for entries in plan.catalogs.values():
        for entry in entries:
            process(entry, entry.values)
    for entry in plan.levels1:
        process(entry, entry.values)
    for entry in plan.levels2:
        incoming = dict(entry.values)
        parent = incoming.pop("nivel1_codigo")
        incoming["nivel1_id"] = targets["NIVEL1"][parent].pk
        for name, entity in (
            ("clase", "CLASE"), ("criticidad", "CRITICIDAD"), ("tipo", "TIPO")
        ):
            label = incoming.pop(name)
            incoming[f"{name}_id"] = None if label is None else targets[entity][label].pk
        process(entry, incoming)
    for issue in plan.orphan_issues:
        write_issue(execution, issue)
    incidences += len(plan.orphan_issues)
    execution.creados = sum(count["creados"] for count in counts.values())
    execution.actualizados = sum(count["actualizados"] for count in counts.values())
    execution.omitidos = sum(count["omitidos"] for count in counts.values())
    execution.observados = (
        sum(count["observados"] for count in counts.values()) + len(plan.orphan_issues)
    )
    execution.filas_continuacion = plan.continuations
    execution.filas_sin_identidad = len(plan.orphan_issues)
    execution.contadores_por_entidad = counts | {
        "FILAS": {
            "fisicas": len(plan.workbook.rows),
            "servicios_explicitos": sum(row.kind == "SERVICIO" for row in plan.workbook.rows),
            "continuaciones": plan.continuations,
            "sin_identidad": len(plan.orphan_issues), "vacias": plan.empty_rows,
        },
        "RESULTADO": {entity: len(values) for entity, values in targets.items()},
        "incidencias": incidences,
    }
    execution.estado = EjecucionImportacion.Estado.COMPLETADA
    execution.fecha_fin = timezone.now()
    execution.save(source="IMPORTACION")


def safe_error(exc):
    if isinstance(exc, CatalogImportError):
        return str(exc)
    if isinstance(exc, ValidationError):
        return "Validación del dominio rechazada durante la importación."
    if isinstance(exc, DatabaseError):
        return "Error PostgreSQL durante la importación."
    return f"Error interno de importación ({type(exc).__name__})."


def import_catalog(file):
    source = read_source(file)
    execution = EjecucionImportacion(
        archivo=source.filename, sha256=source.digest, hoja=SHEET_NAME,
        estado=EjecucionImportacion.Estado.EJECUTANDO,
    )
    execution.save(source="IMPORTACION")
    try:
        plan = prepare(parse_workbook(source))
        with domain_transaction():
            functional_import(execution, plan)
    except Exception as exc:
        # Fuera del bloque fallido: no perder ni escribir en una transacción rota.
        message = safe_error(exc)
        execution.refresh_from_db()
        with domain_transaction():
            execution.estado = EjecucionImportacion.Estado.FALLIDA
            execution.fecha_fin = timezone.now()
            execution.observados = 1
            execution.contadores_por_entidad = {
                "incidencias": 1, "resultado": "ROLLBACK_FUNCIONAL"
            }
            execution.save(source="IMPORTACION")
            write_issue(execution, Issue(
                "FALLO_FATAL", "", "", [],
                {"categoria": type(exc).__name__, "detalle": message},
                "D15: rollback de entidades/procedencia; conservar ejecución fallida.",
                {"accion": "ROLLBACK_FUNCIONAL", "estado": "FALLIDA"},
            ))
        raise CatalogImportError(message, execution.pk) from exc
    return ImportResult(execution)
