"""Atributos JSON declarativos por clasificación; nunca ejecutan texto externo."""

from datetime import date
import math
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address

ATTRIBUTE_TYPES = {"texto", "texto_largo", "entero", "numero", "booleano", "fecha", "ip"}


def validate_value(value, kind):
    valid = False
    if kind in {"texto", "texto_largo"}:
        valid = isinstance(value, str) and (kind == "texto_largo" or len(value) <= 255)
    elif kind == "entero":
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif kind == "numero":
        valid = (
            isinstance(value, int) and not isinstance(value, bool)
            or isinstance(value, float) and math.isfinite(value)
        )
    elif kind == "booleano":
        valid = isinstance(value, bool)
    elif kind == "fecha" and isinstance(value, str):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            try:
                date.fromisoformat(value)
                valid = True
            except ValueError:
                pass
    elif kind == "ip" and isinstance(value, str):
        try:
            validate_ipv46_address(value)
            valid = True
        except ValidationError:
            pass
    if not valid:
        raise ValidationError(f"El valor debe ser de tipo {kind}.")


def validate_schema(schema):
    if not isinstance(schema, dict):
        raise ValidationError("El esquema debe ser un objeto JSON.")
    for key, spec in schema.items():
        if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", key):
            raise ValidationError("Usa claves de atributo en snake_case de hasta 64 caracteres.")
        if not isinstance(spec, dict) or set(spec) - {"tipo", "obligatorio", "opciones"}:
            raise ValidationError(f"Definición inválida del atributo {key}.")
        if not isinstance(spec.get("tipo"), str) or spec["tipo"] not in ATTRIBUTE_TYPES:
            raise ValidationError(f"Tipo de atributo desconocido: {key}.")
        if not isinstance(spec.get("obligatorio", False), bool):
            raise ValidationError(f"Obligatoriedad inválida: {key}.")
        if "opciones" in spec:
            options = spec["opciones"]
            if not isinstance(options, list) or not options:
                raise ValidationError(f"Opciones inválidas: {key}.")
            for value in options:
                validate_value(value, spec["tipo"])


def validate_attributes(values, schema):
    validate_schema(schema)
    if not isinstance(values, dict):
        raise ValidationError("Los atributos deben ser un objeto JSON.")
    if set(values) - set(schema):
        raise ValidationError("Hay atributos no declarados para esta clasificación.")
    errors = []
    for key, spec in schema.items():
        value = values.get(key)
        missing = value is None or value == ""
        if spec.get("obligatorio", False) and (
            missing or isinstance(value, str) and not value.strip()
        ):
            errors.append(f"Falta el atributo obligatorio {key}.")
        elif not missing:
            try:
                validate_value(value, spec["tipo"])
                if "opciones" in spec and not any(
                    type(value) is type(option) and value == option
                    for option in spec["opciones"]
                ):
                    raise ValidationError("El valor no pertenece a las opciones.")
            except ValidationError as error:
                errors.extend(f"{key}: {message}" for message in error.messages)
    if errors:
        raise ValidationError(errors)
