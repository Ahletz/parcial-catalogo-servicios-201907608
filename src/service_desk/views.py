"""Portal del solicitante, consola de agentes, FAQ, tablero y grafo ITSM.

Las vistas solo traducen formularios; toda autorización y regla vive en
servicios/permisos y se vuelve a comprobar en cada POST.
"""

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from accounts.access import functional_access
from accounts.models import Usuario
from processes.catalogo import Proceso, proceso_de
from . import servicios
from .forms import (
    AccionForm, AdjuntoForm, ComentarioForm, ReclasificacionForm, RelacionForm, TicketFiltros,
    TicketForm, TransferenciaForm, codigos_ci, convertir_datos,
)
from cmdb.grafos import disposicion
from .grafos import ORDEN_PROCESO, cadena
from .indicadores import calcular
from .models import ArticuloConocimiento, ColaServiceDesk, Ticket
from .permisos import (
    Capacidad, capacidades, es_solicitante, puede_crear_tickets, puede_ver, puede_ver_internas,
)


def errores(request, error):
    mensajes = error.messages if isinstance(error, ValidationError) else [str(error)]
    for mensaje in mensajes:
        messages.error(request, mensaje)


def filtrar(queryset, filtros):
    datos = filtros.cleaned_data
    if datos["numero"]:
        queryset = queryset.filter(numero__icontains=datos["numero"].strip())
    if datos["servicio"]:
        texto = datos["servicio"].strip()
        queryset = queryset.filter(Q(servicio__codigo__icontains=texto)
                                   | Q(servicio__nombre__icontains=texto))
    for campo in ("proceso", "cola", "prioridad"):
        if datos[campo] not in (None, ""):
            queryset = queryset.filter(**{campo: datos[campo]})
    if datos["estado"]:
        queryset = queryset.filter(estado__iexact=datos["estado"].strip())
    if datos["responsable"]:
        queryset = queryset.filter(
            responsable__identificador__icontains=datos["responsable"].strip())
    if datos["desde"]:
        queryset = queryset.filter(created_at__date__gte=datos["desde"])
    if datos["hasta"]:
        queryset = queryset.filter(created_at__date__lte=datos["hasta"])
    if datos["abiertos"]:
        queryset = queryset.abiertos()
    return queryset


def pagina(request, queryset, por_pagina=25):
    page = Paginator(queryset, por_pagina).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return page, query.urlencode()


@functional_access
@require_safe
def portal(request):
    user = request.user
    colas = [c for c in ColaServiceDesk.objects.filter(estado=True)
             if capacidades(user, c) & {Capacidad.CONSULTAR}]
    return render(request, "service_desk/portal.html", {
        "propios": Ticket.objects.filter(Q(solicitante=user) | Q(creador=user))
        .select_related("servicio")[:10],
        "puede_crear": puede_crear_tickets(user), "colas": colas,
        "articulos": ArticuloConocimiento.objects.filter(publicado=True)[:5],
    })


@functional_access
@require_safe
def ticket_lista(request):
    filtros = TicketFiltros(request.GET or None)
    tickets = servicios.tickets_visibles(request.user).select_related(
        "servicio", "cola", "responsable").en_orden_de_cola()
    if filtros.is_bound:
        tickets = filtrar(tickets, filtros) if filtros.is_valid() else tickets.none()
    page, query = pagina(request, tickets)
    return render(request, "service_desk/tickets.html", {
        "filtros": filtros, "page": page, "query": query,
    })


@functional_access
@require_http_methods(["GET", "POST"])
def ticket_nuevo(request):
    if not puede_crear_tickets(request.user):
        raise PermissionDenied("No puedes registrar tickets.")
    form = TicketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            proceso = proceso_de(datos["tipo"], datos["subtipo"])
            if proceso is None:
                raise ValidationError("El tipo/subtipo no corresponde a ningún proceso.")
            ticket = servicios.crear_ticket(
                request.user, tipo=datos["tipo"], subtipo=datos["subtipo"],
                servicio=datos["servicio"], cola=datos["cola"], titulo=datos["titulo"],
                descripcion=datos["descripcion"], prioridad=datos["prioridad"],
                impacto=datos["impacto"], urgencia=datos["urgencia"], canal=datos["canal"],
                cis=datos["cis"], motivo_sin_ci=datos["motivo_sin_ci"],
                detalle=form.detalle(proceso),
            )
            messages.success(request, f"Ticket {ticket.numero} registrado.")
            return redirect("sd-ticket", numero=ticket.numero)
        except (ValidationError, PermissionDenied, ValueError) as error:
            errores(request, error)
    return render(request, "service_desk/ticket_form.html", {"form": form})


def historial_visible(user, ticket):
    acciones = ticket.acciones.select_related("actor")
    if puede_ver_internas(user, ticket):
        return acciones
    # El solicitante ve estados y su propia interacción, no notas ni datos internos.
    return acciones.filter(Q(campo="estado") | Q(accion="COMENTARIO"))


@functional_access
@require_http_methods(["GET", "POST"])
def ticket_detalle(request, numero):
    ticket = get_object_or_404(Ticket.objects.select_related(
        "servicio__nivel1", "cola", "responsable", "solicitante"), numero=numero)
    user = request.user
    if not puede_ver(user, ticket):
        raise PermissionDenied("No puedes ver este ticket.")
    if request.method == "POST":
        try:
            ejecutar_post(request, ticket)
        except (ValidationError, PermissionDenied, ValueError) as error:
            errores(request, error)
        return redirect("sd-ticket", numero=ticket.numero)
    internas = puede_ver_internas(user, ticket)
    caps = capacidades(user, ticket.cola)
    detalle = ticket.definicion.modelo_detalle().objects.filter(ticket_id=ticket.pk).first()
    campos_detalle = [
        (f.verbose_name, getattr(detalle, f.name)) for f in detalle._meta.concrete_fields
        if f.name not in {"id", "ticket", "created_at", "updated_at", "revision_manual"}
    ] if detalle and internas else []
    return render(request, "service_desk/ticket_detail.html", {
        "ticket": ticket, "internas": internas, "caps": caps,
        "acciones": [
            t for t in ticket.definicion.acciones_desde(ticket.estado)
            if t.accion in servicios.acciones_disponibles(user, ticket)
        ] if ticket.abierto else [],
        "comentarios": servicios.comentarios_visibles(user, ticket).select_related("autor"),
        "adjuntos": servicios.adjuntos_visibles(user, ticket),
        "historial": historial_visible(user, ticket),
        "cis": ticket.cis.all(), "campos_detalle": campos_detalle,
        "relaciones": ticket.relaciones_salientes.select_related("destino"),
        "relaciones_entrantes": ticket.relaciones_entrantes.select_related("origen"),
        "es_solicitante": es_solicitante(user, ticket),
        "puede_comentar": es_solicitante(user, ticket) or internas,
        "formularios": {
            "accion": AccionForm(), "comentario": ComentarioForm(), "adjunto": AdjuntoForm(),
            "transferencia": TransferenciaForm(), "reclasificacion": ReclasificacionForm(),
            "relacion": RelacionForm(),
        },
        "agentes": Usuario.objects.filter(is_active=True, rol=Usuario.Rol.OPERATIVO),
        "evento_con_incidente": ticket.proceso == Proceso.EVENTOS,
    })


def ejecutar_post(request, ticket):
    user, operacion, post = request.user, request.POST.get("operacion"), request.POST
    if operacion == "tomar":
        servicios.tomar_ticket(user, ticket.pk)
    elif operacion == "asignar":
        agente = get_object_or_404(Usuario, pk=post.get("agente"))
        servicios.asignar_ticket(user, ticket.pk, agente, post.get("motivo", ""))
    elif operacion == "accion":
        form = AccionForm(post)
        if not form.is_valid():
            raise ValidationError("Datos de acción inválidos.")
        datos = convertir_datos(ticket, form.cleaned_data["datos"])
        servicios.ejecutar_accion(user, ticket.pk, form.cleaned_data["accion"],
                                  form.cleaned_data["motivo"], datos)
    elif operacion == "comentario":
        form = ComentarioForm(post)
        if not form.is_valid():
            raise ValidationError("Escribe un comentario.")
        servicios.comentar(user, ticket.pk, form.cleaned_data["texto"],
                           form.cleaned_data["interno"])
    elif operacion == "adjunto":
        form = AdjuntoForm(post, request.FILES)
        if not form.is_valid():
            raise ValidationError("Selecciona un archivo.")
        servicios.adjuntar(user, ticket.pk, form.cleaned_data["archivo"],
                           form.cleaned_data["interno"])
    elif operacion == "transferir":
        form = TransferenciaForm(post)
        if not form.is_valid():
            raise ValidationError("Cola y motivo son obligatorios.")
        servicios.transferir_ticket(user, ticket.pk, form.cleaned_data["cola"],
                                    form.cleaned_data["motivo"])
    elif operacion == "reclasificar":
        form = ReclasificacionForm(post)
        if not form.is_valid():
            raise ValidationError("Tipo, cola y motivo son obligatorios.")
        datos = form.cleaned_data
        servicios.reclasificar_ticket(user, ticket.pk, tipo=datos["tipo"],
                                      subtipo=datos["subtipo"], cola_destino=datos["cola"],
                                      motivo=datos["motivo"], detalle=datos["datos"])
    elif operacion == "ci":
        for ci in codigos_ci(post.get("cis", "")):
            servicios.vincular_ci(user, ticket.pk, ci, post.get("observacion", ""))
    elif operacion == "relacion":
        form = RelacionForm(post)
        if not form.is_valid():
            raise ValidationError("Destino y tipo son obligatorios.")
        destino = get_object_or_404(Ticket, numero=form.cleaned_data["destino"].strip())
        servicios.relacionar_tickets(user, ticket.pk, destino.pk, form.cleaned_data["tipo"],
                                     form.cleaned_data["motivo"])
    elif operacion == "incidente":
        incidente, creado = servicios.vincular_incidente_evento(user, ticket.pk)
        messages.info(request, f"Incidente {incidente.numero} "
                               f"{'creado' if creado else 'ya vinculado'}.")
        return
    else:
        raise ValidationError("Operación desconocida.")
    messages.success(request, "Operación registrada.")


@functional_access
@require_safe
def descargar_adjunto(request, identificador):
    """Sesión + autorización por ticket/visibilidad; nunca un enlace público."""
    adjunto = servicios.adjunto_autorizado(request.user, identificador)
    respuesta = FileResponse(
        adjunto.archivo.open("rb"), as_attachment=True,
        filename=adjunto.nombre_original, content_type=adjunto.tipo_mime,
    )
    respuesta["X-Content-Type-Options"] = "nosniff"
    respuesta["Content-Security-Policy"] = "default-src 'none'; sandbox"
    respuesta["Cache-Control"] = "private, no-store"
    return respuesta


@functional_access
@require_safe
def colas(request):
    filas = []
    for cola in ColaServiceDesk.objects.all():
        caps = capacidades(request.user, cola)
        if Capacidad.CONSULTAR in caps:
            abiertos = cola.tickets.abiertos()
            filas.append((cola, sorted(caps), abiertos.count(),
                          abiertos.filter(responsable__isnull=True).count()))
    return render(request, "service_desk/colas.html", {"filas": filas})


@functional_access
@require_http_methods(["GET", "POST"])
def cola_detalle(request, codigo):
    cola = get_object_or_404(ColaServiceDesk, codigo=codigo)
    if request.method == "POST":
        try:
            ticket = servicios.tomar_ticket(request.user, int(request.POST.get("ticket")))
            messages.success(request, f"Tomaste {ticket.numero}.")
        except (ValidationError, PermissionDenied, ValueError, Ticket.DoesNotExist) as error:
            errores(request, error)
        return redirect("sd-cola", codigo=cola.codigo)
    tickets = servicios.tickets_en_cola(request.user, cola).select_related(
        "servicio", "responsable")
    page, query = pagina(request, tickets)
    return render(request, "service_desk/cola.html", {
        "cola": cola, "page": page, "query": query,
        "puede_tomar": Capacidad.ATENDER in capacidades(request.user, cola)
        and request.user.rol != Usuario.Rol.CONSULTA,
    })


@functional_access
@require_safe
def faq(request):
    texto = request.GET.get("q", "").strip()
    articulos = ArticuloConocimiento.objects.all()
    if request.user.rol != Usuario.Rol.ADMINISTRADOR:
        articulos = articulos.filter(publicado=True)
    if texto:
        articulos = articulos.filter(Q(titulo__icontains=texto) | Q(contenido__icontains=texto)
                                     | Q(categoria__icontains=texto))
    page, query = pagina(request, articulos, 20)
    return render(request, "service_desk/faq.html", {"page": page, "query": query, "q": texto})


@functional_access
@require_safe
def faq_detalle(request, pk):
    articulo = get_object_or_404(ArticuloConocimiento, pk=pk)
    if not articulo.publicado and request.user.rol != Usuario.Rol.ADMINISTRADOR:
        raise PermissionDenied("Artículo no publicado.")
    return render(request, "service_desk/faq_detail.html", {"articulo": articulo})


@functional_access
@require_safe
def tablero(request):
    datos = calcular(servicios.tickets_visibles(request.user))
    return render(request, "service_desk/tablero.html", {"d": datos})


@functional_access
@require_safe
def grafo_ticket(request, numero):
    ticket = get_object_or_404(Ticket, numero=numero)
    if not puede_ver(request.user, ticket):
        raise PermissionDenied("No puedes ver este ticket.")
    datos = cadena(request.user, ticket, request.GET.get("profundidad", 4))
    pos, ancho, alto = disposicion(
        [(t.pk, ORDEN_PROCESO.get(t.proceso, 4)) for t in datos["nodos"]])
    nodos = [(t, *pos[t.pk]) for t in datos["nodos"]]
    lineas = [(*pos[o], *pos[d], tipo) for o, d, tipo in datos["aristas"]]
    return render(request, "service_desk/grafo_ticket.html", {
        "g": datos, "svg_nodos": nodos, "svg_lineas": lineas, "ancho": ancho, "alto": alto,
    })
