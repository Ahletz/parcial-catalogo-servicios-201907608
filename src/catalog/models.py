from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from config.domain import DomainModel, NamedStateModel


class Clasificacion(DomainModel):
    etiqueta = models.CharField(max_length=100, unique=True)
    estado = models.BooleanField(default=True)
    state_field = "estado"

    class Meta:
        abstract = True
        ordering = ["etiqueta"]

    def __str__(self):
        return self.etiqueta


class ClaseServicio(Clasificacion):
    pass


class CriticidadServicio(Clasificacion):
    pass


class TipoServicio(Clasificacion):
    pass


class ServicioNivel1(NamedStateModel):
    codigo = models.CharField(max_length=64, unique=True)


class ServicioNivel2(DomainModel):
    class Origen(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        IMPORTADO = "IMPORTADO", "Importado"

    codigo = models.CharField(max_length=64, unique=True)
    nombre = models.CharField(max_length=255)
    nivel1 = models.ForeignKey(
        ServicioNivel1, on_delete=models.PROTECT, related_name="servicios_n2"
    )
    activo = models.BooleanField(null=True, blank=True, default=None)
    clase = models.ForeignKey(
        ClaseServicio, on_delete=models.PROTECT, null=True, blank=True, related_name="servicios"
    )
    criticidad = models.ForeignKey(
        CriticidadServicio, on_delete=models.PROTECT,
        null=True, blank=True, related_name="servicios",
    )
    tipo = models.ForeignKey(
        TipoServicio, on_delete=models.PROTECT, null=True, blank=True, related_name="servicios"
    )
    descripcion = models.TextField(null=True, blank=True)
    metrica = models.TextField(null=True, blank=True)
    minimo = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    maximo = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    seccion_responsable = models.ForeignKey(
        "organization.Seccion", on_delete=models.PROTECT,
        null=True, blank=True, related_name="servicios",
    )
    usuario_responsable = models.ForeignKey(
        "accounts.Usuario", on_delete=models.PROTECT,
        null=True, blank=True, related_name="servicios_responsables",
    )
    origen = models.CharField(
        max_length=9, choices=Origen.choices, default=Origen.MANUAL, editable=False
    )
    state_field = "activo"
    parent_field = "nivel1"

    class Meta:
        ordering = ["codigo"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(minimo__isnull=True) | Q(maximo__isnull=True)
                    | Q(minimo__lte=F("maximo"))
                ),
                name="servicio_umbrales_ordenados",
            ),
            models.CheckConstraint(
                condition=(
                    Q(usuario_responsable__isnull=True)
                    | Q(seccion_responsable__isnull=False)
                ),
                name="servicio_usuario_requiere_seccion",
            ),
            models.CheckConstraint(
                condition=Q(origen="IMPORTADO") | Q(seccion_responsable__isnull=False),
                name="servicio_manual_requiere_seccion",
            ),
            models.CheckConstraint(
                condition=Q(origen__in=["MANUAL", "IMPORTADO"]),
                name="servicio_origen_valido",
            ),
        ]

    def clean(self):
        super().clean()
        if self.origen == self.Origen.MANUAL and self.seccion_responsable_id is None:
            raise ValidationError({"seccion_responsable": "Un servicio manual requiere sección."})
        if self.minimo is not None and self.maximo is not None:
            try:
                minimum, maximum = Decimal(str(self.minimo)), Decimal(str(self.maximo))
                if minimum.is_finite() and maximum.is_finite() and minimum > maximum:
                    raise ValidationError({"minimo": "El mínimo no puede superar al máximo."})
            except InvalidOperation:
                pass  # clean_fields ya informa decimales inválidos.
        for field in ("clase", "criticidad", "tipo", "seccion_responsable", "usuario_responsable"):
            self.validate_active_reference(field)
        if self.usuario_responsable_id is not None:
            user_model = self._meta.get_field("usuario_responsable").related_model
            user = user_model.objects.select_related("puesto").filter(
                pk=self.usuario_responsable_id
            ).first()
            if self.seccion_responsable_id is None or (
                user and user.puesto.seccion_id != self.seccion_responsable_id
            ):
                raise ValidationError({
                    "usuario_responsable": (
                        "El responsable debe pertenecer a la sección del servicio."
                    )
                })

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
