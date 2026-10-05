from django import forms

from config.forms import DomainForm, reference_field
from .models import (
    ClaseServicio, CriticidadServicio, ServicioNivel1, ServicioNivel2, TipoServicio,
)


class NullableBooleanSelect(forms.TypedChoiceField):
    def __init__(self, **kwargs):
        super().__init__(
            choices=[("", "Desconocido"), ("true", "Activo"), ("false", "Inactivo")],
            coerce=lambda value: {"true": True, "false": False}[value],
            empty_value=None, required=False, **kwargs,
        )

    def prepare_value(self, value):
        if value is True:
            return "true"
        if value is False:
            return "false"
        return "" if value is None else value


class ServicioForm(DomainForm):
    activo = NullableBooleanSelect(label="Estado")

    class Meta:
        model = ServicioNivel2
        fields = [
            "codigo", "nombre", "nivel1", "activo", "clase", "criticidad", "tipo",
            "descripcion", "metrica", "minimo", "maximo", "seccion_responsable",
            "usuario_responsable",
        ]
        labels = {
            "codigo": "Código", "nivel1": "Nivel 1", "descripcion": "Descripción",
            "metrica": "Métrica", "minimo": "Mínimo", "maximo": "Máximo",
            "seccion_responsable": "Sección responsable",
            "usuario_responsable": "Usuario responsable",
        }
        formfield_callback = reference_field
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3}),
                   "metrica": forms.Textarea(attrs={"rows": 2})}

    def clean(self):
        data = super().clean()
        for name in ("descripcion", "metrica"):
            if data.get(name) == "":
                data[name] = None
        return data


class ServiceFilters(forms.Form):
    q = forms.CharField(label="Código o nombre", required=False, max_length=255)
    nivel1 = forms.ModelChoiceField(
        label="Nivel 1", queryset=ServicioNivel1.objects.all(), required=False
    )
    estado = forms.ChoiceField(label="Estado", required=False, choices=[
        ("", "Todos"), ("activo", "Activo"), ("inactivo", "Inactivo"),
        ("desconocido", "Desconocido"),
    ])
    clase = forms.ModelChoiceField(queryset=ClaseServicio.objects.all(), required=False)
    criticidad = forms.ModelChoiceField(queryset=CriticidadServicio.objects.all(), required=False)
    tipo = forms.ModelChoiceField(queryset=TipoServicio.objects.all(), required=False)
