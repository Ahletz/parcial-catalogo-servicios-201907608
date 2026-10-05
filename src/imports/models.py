import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q

from config.domain import AppendOnlyModel, DomainModel


def validate_coordinates(record):
    if not isinstance(record.filas, list) or any(
        type(row) is not int or row < 1 for row in record.filas
    ):
        raise ValidationError({"filas": "Usa una lista de números de fila positivos."})
    for name, pattern in (
        ("celdas", r"[A-Z]+[1-9][0-9]*"),
        ("rangos", r"[A-Z]+[1-9][0-9]*:[A-Z]+[1-9][0-9]*"),
    ):
        values = getattr(record, name)
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not re.fullmatch(pattern, value) for value in values
        ):
            raise ValidationError({name: "Usa una lista de coordenadas Excel válidas."})


class EjecucionImportacion(DomainModel):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EJECUTANDO = "EJECUTANDO", "Ejecutando"
        COMPLETADA = "COMPLETADA", "Completada"
        FALLIDA = "FALLIDA", "Fallida"

    archivo = models.CharField(max_length=512)
    sha256 = models.CharField(
        max_length=64, validators=[RegexValidator(r"^[0-9a-f]{64}$", "SHA-256 inválido.")]
    )
    hoja = models.CharField(max_length=120)
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    creados = models.PositiveIntegerField(default=0)
    actualizados = models.PositiveIntegerField(default=0)
    omitidos = models.PositiveIntegerField(default=0)
    observados = models.PositiveIntegerField(default=0)
    filas_continuacion = models.PositiveIntegerField(default=0)
    filas_sin_identidad = models.PositiveIntegerField(default=0)
    contadores_por_entidad = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-fecha"]
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=[
                    "PENDIENTE", "EJECUTANDO", "COMPLETADA", "FALLIDA"
                ]),
                name="ejecucion_estado_valido",
            ),
            models.CheckConstraint(
                condition=Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=F("fecha")),
                name="ejecucion_fechas_ordenadas",
            ),
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.contadores_por_entidad, dict):
            raise ValidationError({"contadores_por_entidad": "Usa un objeto JSON."})


class RegistroOrigen(AppendOnlyModel):
    class Entidad(models.TextChoices):
        NIVEL1 = "NIVEL1", "Servicio nivel 1"
        NIVEL2 = "NIVEL2", "Servicio nivel 2"
        CLASE = "CLASE", "Clase"
        CRITICIDAD = "CRITICIDAD", "Criticidad"
        TIPO = "TIPO", "Tipo"

    ejecucion = models.ForeignKey(
        EjecucionImportacion, on_delete=models.PROTECT, related_name="registros"
    )
    entidad = models.CharField(max_length=10, choices=Entidad.choices)
    codigo = models.CharField(max_length=100)
    servicio_n1 = models.ForeignKey(
        "catalog.ServicioNivel1", on_delete=models.PROTECT,
        null=True, blank=True, related_name="registros_origen",
    )
    servicio_n2 = models.ForeignKey(
        "catalog.ServicioNivel2", on_delete=models.PROTECT,
        null=True, blank=True, related_name="registros_origen",
    )
    hoja = models.CharField(max_length=120)
    filas = models.JSONField(default=list, blank=True)
    celdas = models.JSONField(default=list, blank=True)
    rangos = models.JSONField(default=list, blank=True)
    valores_originales = models.JSONField(default=dict, blank=True)
    valores_importados = models.JSONField(default=dict, blank=True)
    valores_aplicados = models.JSONField(default=dict, blank=True)
    transformaciones = models.JSONField(default=list, blank=True)
    revision_manual_capturada = models.PositiveBigIntegerField(default=0)
    regla_aplicada = models.TextField(blank=True)
    resultado = models.CharField(max_length=64)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(servicio_n1__isnull=True) | Q(servicio_n2__isnull=True),
                name="origen_un_solo_nivel",
            ),
            models.CheckConstraint(
                condition=Q(entidad="NIVEL1") | Q(servicio_n1__isnull=True),
                name="origen_n1_entidad_coherente",
            ),
            models.CheckConstraint(
                condition=Q(entidad="NIVEL2") | Q(servicio_n2__isnull=True),
                name="origen_n2_entidad_coherente",
            ),
            models.CheckConstraint(
                condition=Q(entidad__in=["NIVEL1", "NIVEL2", "CLASE", "CRITICIDAD", "TIPO"]),
                name="origen_entidad_valida",
            ),
        ]

    def clean(self):
        super().clean()
        validate_coordinates(self)
        if not isinstance(self.transformaciones, list):
            raise ValidationError({"transformaciones": "Usa una lista JSON."})
        for name in ("valores_originales", "valores_importados", "valores_aplicados"):
            if not isinstance(getattr(self, name), dict):
                raise ValidationError({name: "Usa un objeto JSON."})
        if self.previous_values() is None:
            for name in ("servicio_n1", "servicio_n2"):
                model = self._meta.get_field(name).related_model
                target = model.objects.filter(pk=getattr(self, f"{name}_id")).first()
                if target and self.codigo != target.codigo:
                    raise ValidationError({
                        "codigo": "El código debe coincidir con el servicio relacionado."
                    })


class IncidenciaImportacion(AppendOnlyModel):
    ejecucion = models.ForeignKey(
        EjecucionImportacion, on_delete=models.PROTECT, related_name="incidencias"
    )
    registro = models.ForeignKey(
        RegistroOrigen, on_delete=models.PROTECT, null=True, blank=True, related_name="incidencias"
    )
    tipo = models.CharField(max_length=64)
    entidad = models.CharField(max_length=10, blank=True)
    codigo = models.CharField(max_length=100, blank=True)
    hoja = models.CharField(max_length=120)
    filas = models.JSONField(default=list, blank=True)
    celdas = models.JSONField(default=list, blank=True)
    rangos = models.JSONField(default=list, blank=True)
    valores = models.JSONField(default=dict, blank=True)
    regla_aplicada = models.TextField()
    resultado = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["id"]

    def clean(self):
        super().clean()
        validate_coordinates(self)
        for name in ("valores", "resultado"):
            if not isinstance(getattr(self, name), dict):
                raise ValidationError({name: "Usa un objeto JSON."})
        if self.registro_id:
            record = RegistroOrigen.objects.filter(pk=self.registro_id).first()
            if record and record.ejecucion_id != self.ejecucion_id:
                raise ValidationError({"registro": "El origen pertenece a otra ejecución."})
