from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from catalog.models import ServicioNivel2
from cmdb.models import CI
from processes.catalogo import (
    Afectacion, Canal, Nivel, Prioridad, Proceso, SubtipoRequisicion, TipoTicket,
)
from processes.models import DetalleAcceso
from .models import ColaServiceDesk, RelacionTicket


def codigos_ci(texto):
    codigos = [c.strip() for c in (texto or "").replace("\n", ",").split(",") if c.strip()]
    cis = list(CI.objects.filter(codigo__in=codigos, estado=True))
    faltan = set(codigos) - {ci.codigo for ci in cis}
    if faltan:
        raise ValidationError(f"CI inexistentes o inactivos: {', '.join(sorted(faltan))}.")
    return cis


class TicketForm(forms.Form):
    tipo = forms.ChoiceField(choices=TipoTicket.choices)
    subtipo = forms.ChoiceField(choices=[("", "—")] + SubtipoRequisicion.choices, required=False)
    servicio = forms.ModelChoiceField(ServicioNivel2.objects.filter(activo=True).order_by("codigo"))
    cola = forms.ModelChoiceField(ColaServiceDesk.objects.filter(estado=True))
    titulo = forms.CharField(max_length=200)
    descripcion = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
    prioridad = forms.TypedChoiceField(choices=Prioridad.choices, coerce=int,
                                       initial=Prioridad.MEDIA)
    impacto = forms.ChoiceField(choices=Nivel.choices, initial=Nivel.MEDIO)
    urgencia = forms.ChoiceField(choices=Nivel.choices, initial=Nivel.MEDIO)
    canal = forms.ChoiceField(choices=Canal.choices, initial=Canal.PORTAL)
    cis = forms.CharField(label="Códigos de CI (separados por coma)", required=False)
    motivo_sin_ci = forms.CharField(label="Motivo si no hay CI", required=False,
                                    widget=forms.Textarea(attrs={"rows": 2}))
    necesidad = forms.CharField(label="Necesidad (nuevo servicio)", required=False,
                                widget=forms.Textarea(attrs={"rows": 2}))
    clave_evento = forms.CharField(label="Clave del evento", required=False)
    fuente = forms.CharField(label="Fuente del evento", required=False)
    afectacion = forms.ChoiceField(label="Afectación (incidente)", required=False,
                                   choices=[("", "—")] + Afectacion.choices)
    beneficiario = forms.CharField(label="Beneficiario (identificador, acceso)", required=False)
    recurso = forms.CharField(label="Recurso (acceso)", required=False)
    permiso = forms.CharField(label="Permiso (acceso)", required=False)
    accion = forms.ChoiceField(label="Acción (acceso)", required=False,
                               choices=[("", "—")] + DetalleAcceso.Accion.choices)

    CAMPOS_PROCESO = {
        Proceso.NUEVOS_SERVICIOS: ("necesidad",),
        Proceso.EVENTOS: ("clave_evento", "fuente"),
        Proceso.INCIDENTES: ("afectacion",),
        Proceso.ACCESOS: ("beneficiario", "recurso", "permiso", "accion"),
    }

    def clean_cis(self):
        return codigos_ci(self.cleaned_data["cis"])

    def detalle(self, proceso):
        from accounts.models import Usuario

        datos = {c: self.cleaned_data[c] for c in self.CAMPOS_PROCESO.get(proceso, ())
                 if self.cleaned_data.get(c)}
        if "beneficiario" in datos:
            datos["beneficiario"] = Usuario.objects.filter(
                identificador=datos["beneficiario"].strip().casefold()).first()
            if datos["beneficiario"] is None:
                raise ValidationError("Beneficiario inexistente.")
        return datos


class DatosField(forms.CharField):
    """Líneas campo=valor; el servicio solo acepta los campos de la transición."""

    widget = forms.Textarea(attrs={"rows": 3, "placeholder": "campo=valor"})

    def to_python(self, value):
        datos = {}
        for linea in (value or "").splitlines():
            if not linea.strip():
                continue
            if "=" not in linea:
                raise ValidationError(f"Línea sin «=»: {linea}")
            campo, valor = linea.split("=", 1)
            datos[campo.strip()] = valor.strip()
        return datos


def convertir_datos(ticket, datos):
    """Convierte texto al tipo del campo del detalle o del ticket."""
    detalle_model = ticket.definicion.modelo_detalle()
    convertidos = {}
    for nombre, valor in datos.items():
        modelo = type(ticket) if nombre in {"resolucion", "prioridad"} else detalle_model
        try:
            campo = modelo._meta.get_field(nombre)
        except Exception as error:
            raise ValidationError(f"Campo desconocido: {nombre}.") from error
        if campo.is_relation:
            convertidos[nombre] = campo.target_field.to_python(valor) if valor else None
            continue
        convertido = campo.to_python(valor) if valor != "" or not campo.null else None
        if isinstance(convertido, datetime) and timezone.is_naive(convertido):
            convertido = timezone.make_aware(convertido)
        convertidos[nombre] = convertido
    return convertidos


class AccionForm(forms.Form):
    accion = forms.CharField()
    motivo = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
    datos = DatosField(required=False)


class ComentarioForm(forms.Form):
    texto = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    interno = forms.BooleanField(required=False, label="Nota interna")


class AdjuntoForm(forms.Form):
    archivo = forms.FileField()
    interno = forms.BooleanField(required=False, label="Solo interno")


class TransferenciaForm(forms.Form):
    cola = forms.ModelChoiceField(ColaServiceDesk.objects.filter(estado=True))
    motivo = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}))


class ReclasificacionForm(forms.Form):
    tipo = forms.ChoiceField(choices=TipoTicket.choices)
    subtipo = forms.ChoiceField(choices=[("", "—")] + SubtipoRequisicion.choices, required=False)
    cola = forms.ModelChoiceField(ColaServiceDesk.objects.filter(estado=True))
    motivo = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}))
    datos = DatosField(required=False, label="Datos de alta del nuevo proceso")


class RelacionForm(forms.Form):
    destino = forms.CharField(label="Número del ticket destino (SD-000001)")
    tipo = forms.ChoiceField(choices=RelacionTicket.Tipo.choices)
    motivo = forms.CharField(required=False)


class TicketFiltros(forms.Form):
    numero = forms.CharField(required=False)
    servicio = forms.CharField(required=False, label="Servicio (código o nombre)")
    proceso = forms.ChoiceField(required=False, choices=[("", "Todos")] + Proceso.choices)
    cola = forms.ModelChoiceField(ColaServiceDesk.objects.all(), required=False)
    estado = forms.CharField(required=False)
    prioridad = forms.TypedChoiceField(required=False, coerce=int, empty_value=None,
                                       choices=[("", "Todas")] + Prioridad.choices)
    responsable = forms.CharField(required=False, label="Responsable (identificador)")
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    abiertos = forms.BooleanField(required=False, label="Solo abiertos")
