"""CMDB de solo lectura para usuarios funcionales; la edición es del admin."""

from django import forms
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from accounts.access import functional_access
from service_desk.permisos import puede_ver
from .grafos import disposicion, impacto
from .models import CI, ClasificacionCI, UbicacionCI


class FiltrosCI(forms.Form):
    q = forms.CharField(required=False, label="Código o nombre")
    clasificacion = forms.ModelChoiceField(ClasificacionCI.objects.all(), required=False)
    estado = forms.ChoiceField(required=False, choices=[
        ("", "Todos"), ("activo", "Activo"), ("inactivo", "Inactivo")])
    ubicacion = forms.ModelChoiceField(UbicacionCI.objects.all(), required=False)
    responsable = forms.CharField(required=False, label="Responsable (identificador)")
    servicio = forms.CharField(required=False, label="Servicio (código)")


def filtrar_cis(datos):
    cis = CI.objects.select_related("clasificacion", "ubicacion", "responsable")
    if datos.get("q"):
        cis = cis.filter(Q(codigo__icontains=datos["q"]) | Q(nombre__icontains=datos["q"]))
    if datos.get("clasificacion"):
        cis = cis.filter(Q(clasificacion=datos["clasificacion"])
                         | Q(clasificacion__padre=datos["clasificacion"]))
    if datos.get("estado"):
        cis = cis.filter(estado=datos["estado"] == "activo")
    if datos.get("ubicacion"):
        cis = cis.filter(ubicacion=datos["ubicacion"])
    if datos.get("responsable"):
        cis = cis.filter(responsable__identificador__icontains=datos["responsable"])
    if datos.get("servicio"):
        cis = cis.filter(vinculos_servicio__servicio__codigo__iexact=datos["servicio"].strip(),
                         vinculos_servicio__estado=True)
    return cis.order_by("codigo")


@functional_access
@require_safe
def ci_lista(request):
    filtros = FiltrosCI(request.GET or None)
    datos = filtros.cleaned_data if filtros.is_valid() else {}
    page = Paginator(filtrar_cis(datos) if not filtros.is_bound or filtros.is_valid()
                     else CI.objects.none(), 50).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return render(request, "cmdb/lista.html", {
        "filtros": filtros, "page": page, "query": query.urlencode(),
    })


@functional_access
@require_safe
def ci_detalle(request, codigo):
    ci = get_object_or_404(CI.objects.select_related(
        "clasificacion", "ubicacion", "responsable"), codigo=codigo)
    return render(request, "cmdb/detalle.html", {
        "ci": ci, "ruta": ci.clasificacion.ruta(),
        "salientes": ci.relaciones_salientes.select_related("tipo", "destino"),
        "entrantes": ci.relaciones_entrantes.select_related("tipo", "origen"),
        "servicios": ci.vinculos_servicio.select_related("servicio"),
        "tickets": [t for t in ci.tickets.select_related("cola")[:100]
                    if puede_ver(request.user, t)][:20],
    })


@functional_access
@require_safe
def ci_grafo(request, codigo):
    ci = get_object_or_404(CI, codigo=codigo)
    datos = impacto(ci, request.GET.get("profundidad", 3) or 3)
    pos, ancho, alto = disposicion([(c.pk, nivel) for c, nivel in datos["nodos"]])
    nodos = [(c, nivel, *pos[c.pk]) for c, nivel in datos["nodos"]]
    lineas = [(*pos[o], *pos[d], tipo) for o, d, tipo in datos["aristas"]
              if o in pos and d in pos]
    return render(request, "cmdb/grafo.html", {
        "g": datos, "svg_nodos": nodos, "svg_lineas": lineas, "ancho": ancho, "alto": alto,
    })
