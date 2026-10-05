"""Mantenimientos explícitos y reutilizables sobre los modelos aprobados."""

from dataclasses import dataclass

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from accounts.access import functional_access
from accounts.forms import UsuarioForm
from accounts.models import Usuario
from catalog.forms import ServiceFilters, ServicioForm
from catalog.models import (
    ClaseServicio, CriticidadServicio, ServicioNivel1, ServicioNivel2, TipoServicio,
)
from organization.models import Area, Departamento, Empresa, Puesto, Seccion
from .domain import domain_transaction
from .forms import DomainForm, add_domain_errors, reference_field


@dataclass(frozen=True)
class Entity:
    title: str
    model: type
    form: type
    columns: tuple


def entity(title, model, fields, columns):
    return Entity(title, model, modelform_factory(
        model, form=DomainForm, fields=fields, formfield_callback=reference_field,
        labels={"codigo": "Código", "area": "Área", "seccion": "Sección"},
    ), columns)


COMMON = (("codigo", "Código"), ("nombre", "Nombre"), ("estado", "Estado"))
ENTITIES = {
    "empresas": entity("Empresas", Empresa, ["codigo", "nombre", "estado"], COMMON),
    "areas": entity("Áreas", Area, ["codigo", "nombre", "estado", "empresa"],
                    COMMON + (("empresa", "Empresa"),)),
    "departamentos": entity("Departamentos", Departamento,
                            ["codigo", "nombre", "estado", "area"],
                            COMMON + (("area", "Área"),)),
    "secciones": entity("Secciones", Seccion,
                        ["codigo", "nombre", "estado", "departamento"],
                        COMMON + (("departamento", "Departamento"),)),
    "puestos": entity("Puestos", Puesto, ["codigo", "nombre", "estado", "seccion"],
                      COMMON + (("seccion", "Sección"),)),
    "usuarios": Entity("Usuarios", Usuario, UsuarioForm, (
        ("identificador", "Usuario o correo"), ("nombre", "Nombre"), ("rol", "Rol"),
        ("puesto", "Puesto"), ("empresa", "Empresa"), ("is_active", "Estado"),
    )),
    "nivel1": entity("Servicios de nivel 1", ServicioNivel1,
                     ["codigo", "nombre", "estado"], COMMON),
    "servicios": Entity("Servicios de nivel 2", ServicioNivel2, ServicioForm, (
        ("codigo", "Código"), ("nombre", "Nombre"), ("nivel1", "Nivel 1"),
        ("activo", "Estado"), ("seccion_responsable", "Sección responsable"),
    )),
}
for slug, title, model in (
    ("clases", "Clases", ClaseServicio),
    ("criticidades", "Criticidades", CriticidadServicio),
    ("tipos", "Tipos", TipoServicio),
):
    ENTITIES[slug] = entity(title, model, ["etiqueta", "estado"],
                            (("etiqueta", "Etiqueta"), ("estado", "Estado")))


def configuration(slug):
    if slug not in ENTITIES:
        raise Http404("Mantenimiento inexistente.")
    return ENTITIES[slug]


def display(obj, name):
    value = getattr(obj, name)
    if value is None:
        return "Desconocido" if name == "activo" else "Sin informar"
    if isinstance(value, bool):
        return "Activo" if value else "Inactivo"
    choices = getattr(obj, f"get_{name}_display", None)
    return choices() if choices else value


@functional_access
@require_safe
def home(request):
    return render(request, "home.html", {
        "n1": ServicioNivel1.objects.count(), "n2": ServicioNivel2.objects.count(),
        "empresas": Empresa.objects.count(), "usuarios": Usuario.objects.count(),
    })


@functional_access
@require_safe
def organization(request):
    return render(request, "index.html", {"title": "Organización", "entities": [
        (slug, ENTITIES[slug].title) for slug in
        ("empresas", "areas", "departamentos", "secciones", "puestos")
    ]})


@functional_access
@require_safe
def classifications(request):
    return render(request, "index.html", {"title": "Clasificaciones", "entities": [
        (slug, ENTITIES[slug].title) for slug in ("clases", "criticidades", "tipos")
    ]})


@functional_access
@require_safe
def entity_list(request, entity):
    config = configuration(entity)
    queryset = config.model.objects.all().select_related()
    filters = None
    if entity == "servicios":
        filters = ServiceFilters(request.GET)
        if filters.is_valid():
            criteria = filters.cleaned_data
            if criteria["q"]:
                queryset = queryset.filter(
                    Q(codigo__icontains=criteria["q"]) | Q(nombre__icontains=criteria["q"])
                )
            for name in ("nivel1", "clase", "criticidad", "tipo"):
                if criteria[name]:
                    queryset = queryset.filter(**{name: criteria[name]})
            if criteria["estado"]:
                state = {"activo": True, "inactivo": False, "desconocido": None}
                queryset = queryset.filter(activo=state[criteria["estado"]])
        else:
            queryset = queryset.none()
    page = Paginator(queryset.order_by("pk"), 20).get_page(request.GET.get("page"))
    rows = [(obj.pk, [display(obj, name) for name, _ in config.columns]) for obj in page]
    query = request.GET.copy()
    query.pop("page", None)
    return render(request, "list.html", {
        "title": config.title, "entity": entity,
        "headers": [label for _, label in config.columns], "rows": rows,
        "page": page, "query": query.urlencode(), "filters": filters,
    })


@functional_access(write=True)
@require_http_methods(["GET", "POST"])
def entity_form(request, entity, pk=None):
    config = configuration(entity)
    instance = get_object_or_404(config.model, pk=pk) if pk is not None else None
    form = config.form(request.POST if request.method == "POST" else None, instance=instance)
    if request.method == "POST":
        try:
            with domain_transaction():
                if form.is_valid():
                    saved = form.save()
                    messages.success(request, "Registro guardado correctamente.")
                    if entity == "servicios":
                        return redirect("service-detail", pk=saved.pk)
                    return redirect("entity-list", entity=entity)
        except ValidationError as error:
            add_domain_errors(form, error)
        except IntegrityError:
            form.add_error(None, "Código duplicado o referencia inválida; revisa los datos.")
    return render(request, "form.html", {
        "title": ("Editar: " if pk else "Crear: ") + config.title,
        "entity": entity, "form": form,
    })


@functional_access(write=True)
@require_http_methods(["GET", "POST"])
def deactivate(request, entity, pk):
    config = configuration(entity)
    obj = get_object_or_404(config.model, pk=pk)
    errors = []
    if request.method == "POST":
        try:
            with domain_transaction():
                obj.desactivar()
            messages.success(request, "Registro desactivado; se conserva su información.")
            return redirect("entity-list", entity=entity)
        except ValidationError as error:
            errors = error.messages
    return render(request, "deactivate.html", {
        "title": "Desactivar registro", "entity": entity, "object": obj, "errors": errors,
    })


@functional_access
@require_safe
def service_detail(request, pk):
    service = get_object_or_404(ServicioNivel2.objects.select_related(), pk=pk)
    attributes = [
        ("id", "Identificador"), ("codigo", "Código"), ("nombre", "Nombre"),
        ("nivel1", "Nivel 1"), ("activo", "Estado"), ("clase", "Clase"),
        ("criticidad", "Criticidad"), ("tipo", "Tipo"), ("descripcion", "Descripción"),
        ("metrica", "Métrica"), ("minimo", "Mínimo"), ("maximo", "Máximo"),
        ("seccion_responsable", "Sección responsable"),
        ("usuario_responsable", "Usuario responsable"),
    ]
    return render(request, "detail.html", {
        "title": "Ficha del servicio", "service": service,
        "attributes": [(label, display(service, name)) for name, label in attributes],
    })
