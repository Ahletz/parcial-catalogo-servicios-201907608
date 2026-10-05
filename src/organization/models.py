from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models

from config.domain import NamedStateModel


class Empresa(NamedStateModel):
    codigo = models.CharField(max_length=64, unique=True)


class Area(NamedStateModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="areas")
    parent_field = "empresa"

    class Meta(NamedStateModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["empresa", "codigo"], name="area_empresa_codigo_uniq"),
        ]


class Departamento(NamedStateModel):
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="departamentos")
    parent_field = "area"

    class Meta(NamedStateModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["area", "codigo"], name="departamento_area_codigo_uniq"
            ),
        ]


class Seccion(NamedStateModel):
    departamento = models.ForeignKey(
        Departamento, on_delete=models.PROTECT, related_name="secciones"
    )
    parent_field = "departamento"

    class Meta(NamedStateModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["departamento", "codigo"], name="seccion_departamento_codigo_uniq"
            ),
        ]


class Puesto(NamedStateModel):
    seccion = models.ForeignKey(Seccion, on_delete=models.PROTECT, related_name="puestos")
    parent_field = "seccion"

    class Meta(NamedStateModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["seccion", "codigo"], name="puesto_seccion_codigo_uniq"
            ),
        ]

    def clean(self):
        super().clean()
        previous = self.previous_values()
        if previous and previous["seccion_id"] != self.seccion_id:
            service = apps.get_model("catalog", "ServicioNivel2")
            if service.objects.filter(
                usuario_responsable__puesto_id=self.pk
            ).exclude(seccion_responsable_id=self.seccion_id).exists():
                raise ValidationError({
                    "seccion": (
                        "El traslado invalida responsables; "
                        "resuelve sus asignaciones primero."
                    )
                })
