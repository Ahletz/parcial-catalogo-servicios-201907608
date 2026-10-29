import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Max, Q

from config.domain import (
    AppendOnlyModel, DomainModel, DomainQuerySet, NamedStateModel, domain_transaction,
)
from processes.catalogo import (
    Canal, Nivel, NivelSoporte, Prioridad, Proceso, SubtipoRequisicion, TipoTicket,
    proceso_de,
)
from processes.definiciones import DEFINICIONES
from .adjuntos import almacen_adjuntos, ruta_adjunto


class RolServiceDesk(models.TextChoices):
    """Roles operativos aditivos; admin y consulta siguen en Usuario.rol."""

    SOLICITANTE = "SOLICITANTE", "Solicitante"
    AGENTE = "AGENTE", "Agente"
    APROBADOR = "APROBADOR", "Aprobador"


class ColaServiceDesk(NamedStateModel):
    class Orden(models.TextChoices):
        PRIORIDAD_ANTIGUEDAD = "PRIORIDAD_ANTIGUEDAD", "Prioridad y antigüedad"

    codigo = models.CharField(max_length=64, unique=True)
    descripcion = models.TextField(blank=True)
    proceso = models.CharField(max_length=20, choices=Proceso.choices)
    nivel_soporte = models.PositiveSmallIntegerField(
        choices=NivelSoporte.choices, default=NivelSoporte.HELP_DESK
    )
    regla_ordenamiento = models.CharField(
        max_length=20, choices=Orden.choices, default=Orden.PRIORIDAD_ANTIGUEDAD
    )
    objetivo_primera_atencion = models.DurationField(null=True, blank=True)
    objetivo_resolucion = models.DurationField(null=True, blank=True)

    class Meta(NamedStateModel.Meta):
        verbose_name = "cola de Service Desk"
        verbose_name_plural = "colas de Service Desk"
        constraints = [
            models.CheckConstraint(
                condition=Q(nivel_soporte__lte=4), name="cola_nivel_soporte_0_4"
            ),
        ]

    def clean(self):
        super().clean()
        previous = self.previous_values()
        if not previous:
            return
        if previous["proceso"] != self.proceso and self.tickets.exists():
            raise ValidationError({"proceso": "La cola ya tiene tickets de su proceso."})
        if previous["estado"] and not self.estado and self.tickets.abiertos().exists():
            raise ValidationError({
                "estado": "Tiene tickets abiertos; transfiérelos antes de desactivar."
            })


class AsignacionRolSD(DomainModel):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="roles_sd"
    )
    rol = models.CharField(max_length=11, choices=RolServiceDesk.choices)
    activo = models.BooleanField(default=True)
    state_field = "activo"

    class Meta:
        ordering = ["usuario_id", "rol"]
        constraints = [
            models.UniqueConstraint(fields=["usuario", "rol"], name="rolsd_usuario_rol_uniq"),
        ]

    def clean(self):
        super().clean()
        previous = self.previous_values()
        if previous and (previous["usuario_id"], previous["rol"]) != (self.usuario_id, self.rol):
            raise ValidationError("Registra otra asignación en lugar de cambiar la existente.")
        if previous and previous["activo"] and not self.activo:
            colas = MembresiaCola.objects.filter(
                rol=self.rol, activo=True, puede_atender=True
            ).values("cola_id")
            if Ticket.objects.abiertos().filter(
                responsable_id=self.usuario_id, cola_id__in=colas
            ).exists():
                raise ValidationError(
                    "El rol sostiene tickets abiertos asignados; reasígnalos primero."
                )


class MembresiaCola(DomainModel):
    """Capacidades sobre una cola para un usuario o para un rol SD (exactamente uno)."""

    cola = models.ForeignKey(ColaServiceDesk, on_delete=models.PROTECT, related_name="membresias")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="membresias_cola",
    )
    rol = models.CharField(max_length=11, choices=RolServiceDesk.choices, blank=True)
    puede_consultar = models.BooleanField(default=True)
    puede_atender = models.BooleanField(default=False)
    puede_transferir = models.BooleanField(default=False)
    puede_aprobar = models.BooleanField(default=False)
    puede_administrar = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    state_field = "activo"

    class Meta:
        ordering = ["cola_id", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(usuario__isnull=False) & Q(rol=""))
                | (Q(usuario__isnull=True) & ~Q(rol="")),
                name="membresia_un_sujeto",
            ),
            models.UniqueConstraint(
                fields=["cola", "usuario"], condition=Q(usuario__isnull=False),
                name="membresia_cola_usuario_uniq",
            ),
            models.UniqueConstraint(
                fields=["cola", "rol"], condition=~Q(rol=""), name="membresia_cola_rol_uniq",
            ),
        ]

    def clean(self):
        super().clean()
        if (self.usuario_id is None) == (self.rol == ""):
            raise ValidationError("Indica exactamente un usuario o un rol.")
        previous = self.previous_values()
        if previous and (
            previous["cola_id"], previous["usuario_id"], previous["rol"]
        ) != (self.cola_id, self.usuario_id, self.rol):
            raise ValidationError("El sujeto y la cola no cambian; crea otra membresía.")
        if previous is None:
            self.validate_active_reference("cola")
        elif previous["activo"] and previous["puede_atender"] and not (
            self.activo and self.puede_atender
        ):
            # Conservador: no deja responsables sin capacidad en tickets abiertos.
            if self.usuario_id:
                afectados = Q(responsable_id=self.usuario_id)
            else:
                afectados = Q(responsable__roles_sd__rol=self.rol,
                              responsable__roles_sd__activo=True)
            if Ticket.objects.abiertos().filter(afectados, cola_id=self.cola_id).exists():
                raise ValidationError(
                    "Hay tickets abiertos asignados que dependen de esta capacidad; "
                    "reasígnalos o transfiérelos primero."
                )


class TicketQuerySet(DomainQuerySet):
    def abiertos(self):
        return self.filter(fecha_cierre__isnull=True)

    def en_orden_de_cola(self):
        """Orden determinista: prioridad, antigüedad y PK como desempate."""
        return self.order_by("prioridad", "created_at", "pk")


class Ticket(DomainModel):
    identificador = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    secuencia = models.PositiveIntegerField(unique=True, editable=False)
    numero = models.CharField(max_length=16, unique=True, editable=False)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_solicitados"
    )
    creador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_creados"
    )
    servicio = models.ForeignKey(
        "catalog.ServicioNivel2", on_delete=models.PROTECT, related_name="tickets"
    )
    tipo = models.CharField(max_length=20, choices=TipoTicket.choices)
    subtipo = models.CharField(max_length=18, choices=SubtipoRequisicion.choices, blank=True)
    proceso = models.CharField(max_length=20, choices=Proceso.choices)
    cola = models.ForeignKey(ColaServiceDesk, on_delete=models.PROTECT, related_name="tickets")
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="tickets_asignados",
    )
    estado = models.CharField(max_length=32)
    prioridad = models.PositiveSmallIntegerField(choices=Prioridad.choices)
    impacto = models.CharField(max_length=5, choices=Nivel.choices)
    urgencia = models.CharField(max_length=5, choices=Nivel.choices)
    canal = models.CharField(max_length=10, choices=Canal.choices)
    resolucion = models.TextField(blank=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    motivo_sin_ci = models.TextField(blank=True)
    cis = models.ManyToManyField("cmdb.CI", through="TicketCI", related_name="tickets", blank=True)
    objects = TicketQuerySet.as_manager()
    INMUTABLES = ("solicitante_id", "creador_id", "servicio_id", "tipo", "subtipo", "proceso")

    class Meta:
        ordering = ["prioridad", "created_at", "pk"]
        indexes = [
            models.Index(fields=["cola", "fecha_cierre", "prioridad", "created_at"],
                         name="ticket_cola_orden_idx"),
            models.Index(fields=["proceso", "estado"], name="ticket_proceso_estado_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_cierre__isnull=True) | Q(fecha_resolucion__isnull=False),
                name="ticket_cierre_requiere_resolucion",
            ),
            models.CheckConstraint(
                condition=Q(fecha_resolucion__isnull=True)
                | Q(fecha_resolucion__gte=F("created_at")),
                name="ticket_resolucion_posterior",
            ),
            models.CheckConstraint(
                condition=Q(prioridad__gte=1, prioridad__lte=4), name="ticket_prioridad_valida",
            ),
        ]

    @property
    def nivel1(self):
        return self.servicio.nivel1

    @property
    def definicion(self):
        return DEFINICIONES[self.proceso]

    @property
    def abierto(self):
        return self.fecha_cierre is None

    def save(self, *args, **kwargs):
        with domain_transaction(kwargs.get("using") or "default"):
            if self.secuencia is None:
                # Seguro: domain_transaction serializa todas las escrituras del dominio.
                ultimo = Ticket.objects.aggregate(m=Max("secuencia"))["m"] or 0
                self.secuencia = ultimo + 1
                self.numero = f"SD-{self.secuencia:06d}"
            return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        previous = self.previous_values()
        proceso = proceso_de(self.tipo, self.subtipo)
        if proceso is None:
            raise ValidationError({"subtipo": "Tipo/subtipo sin proceso asignado."})
        if self.proceso != proceso:
            raise ValidationError({"proceso": f"El tipo corresponde al proceso {proceso}."})
        definicion = DEFINICIONES[self.proceso]
        if self.estado not in definicion.estados:
            raise ValidationError({"estado": "Estado inexistente en el proceso."})
        if previous is None:
            if self.estado != definicion.estado_inicial:
                raise ValidationError({"estado": "El ticket empieza en el estado inicial."})
            for campo in ("servicio", "solicitante", "creador"):
                self.validate_active_reference(campo)
        else:
            cambiados = [n for n in self.INMUTABLES if previous[n] != getattr(self, n)]
            reclasifica = getattr(self, "_reclasificacion", False)
            if reclasifica:
                cambiados = [n for n in cambiados if n not in {"tipo", "subtipo", "proceso"}]
            if cambiados:
                raise ValidationError(f"Campos inmutables tras el alta: {', '.join(cambiados)}.")
            if reclasifica:
                if self.estado != definicion.estado_inicial:
                    raise ValidationError({"estado": "La reclasificación reinicia el flujo."})
            elif previous["estado"] != self.estado:
                if not definicion.es_transicion(previous["estado"], self.estado):
                    raise ValidationError({"estado": "Transición no definida en el proceso."})
                if self.estado in definicion.estados_con_aprobacion:
                    self._exigir_aprobacion()
            if previous["fecha_cierre"] is not None and previous["estado"] == self.estado:
                if any(previous[c] != getattr(self, c) for c in ("cola_id", "responsable_id")):
                    raise ValidationError("Un ticket cerrado no se reasigna ni transfiere.")
        if previous is None or previous["cola_id"] != self.cola_id:
            self.validate_active_reference("cola")
            cola = ColaServiceDesk.objects.get(pk=self.cola_id)
            if cola.proceso != self.proceso:
                raise ValidationError({"cola": "La cola pertenece a otro proceso."})
        if self.responsable_id and (
            previous is None or previous["responsable_id"] != self.responsable_id
            or previous["cola_id"] != self.cola_id
        ):
            self._validar_responsable()
        if (self.estado in definicion.finales) != (self.fecha_cierre is not None):
            raise ValidationError({"fecha_cierre": "Solo los estados finales tienen cierre."})

    def inicio_ciclo_proceso(self):
        """Las aprobaciones de un proceso anterior no valen tras reclasificar."""
        ultima = ReclasificacionTicket.objects.filter(ticket_id=self.pk).order_by("-pk").first()
        return ultima.created_at if ultima else self.created_at

    def _exigir_aprobacion(self):
        from processes.models import Aprobacion

        ultima = Aprobacion.objects.filter(
            ticket_id=self.pk, created_at__gte=self.inicio_ciclo_proceso()
        ).order_by("-pk").first()
        if ultima is None or ultima.decision != Aprobacion.Decision.APROBADA:
            raise ValidationError({"estado": "El estado exige aprobación previa vigente."})

    def _validar_responsable(self):
        from .permisos import Capacidad, capacidades

        self.validate_active_reference("responsable")
        responsable = self._meta.get_field("responsable").related_model.objects.get(
            pk=self.responsable_id
        )
        cola = ColaServiceDesk.objects.get(pk=self.cola_id)
        if Capacidad.ATENDER not in capacidades(responsable, cola):
            raise ValidationError({
                "responsable": "El responsable necesita capacidad de atender en la cola."
            })

    def __str__(self):
        return f"{self.numero} - {self.titulo}"


class TicketCI(AppendOnlyModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="vinculos_ci")
    ci = models.ForeignKey("cmdb.CI", on_delete=models.PROTECT, related_name="vinculos_ticket")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(fields=["ticket", "ci"], name="ticketci_par_uniq"),
        ]

    def clean(self):
        super().clean()
        if self.previous_values() is None:
            self.validate_active_reference("ci")


class RelacionTicket(AppendOnlyModel):
    class Tipo(models.TextChoices):
        EVENTO_INCIDENTE = "EVENTO_INCIDENTE", "Evento genera/vincula incidente"
        INCIDENTE_PROBLEMA = "INCIDENTE_PROBLEMA", "Incidente asociado a problema"
        PROBLEMA_CAMBIO = "PROBLEMA_CAMBIO", "Problema corregido por cambio"
        RELACIONADO = "RELACIONADO", "Relacionado"

    EXTREMOS = {
        Tipo.EVENTO_INCIDENTE: (Proceso.EVENTOS, Proceso.INCIDENTES),
        Tipo.INCIDENTE_PROBLEMA: (Proceso.INCIDENTES, Proceso.PROBLEMAS),
        Tipo.PROBLEMA_CAMBIO: (Proceso.PROBLEMAS, Proceso.CAMBIOS),
    }

    origen = models.ForeignKey(
        Ticket, on_delete=models.PROTECT, related_name="relaciones_salientes"
    )
    destino = models.ForeignKey(
        Ticket, on_delete=models.PROTECT, related_name="relaciones_entrantes"
    )
    tipo = models.CharField(max_length=18, choices=Tipo.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    motivo = models.TextField(blank=True)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["origen", "destino", "tipo"], name="relacionticket_uniq"
            ),
            models.UniqueConstraint(
                fields=["origen"], condition=Q(tipo="EVENTO_INCIDENTE"),
                name="relacionticket_un_incidente_por_evento",
            ),
            models.CheckConstraint(
                condition=~Q(origen=F("destino")), name="relacionticket_no_autorrelacion"
            ),
        ]

    def clean(self):
        super().clean()
        if self.origen_id == self.destino_id:
            raise ValidationError("Un ticket no se relaciona consigo mismo.")
        extremos = self.EXTREMOS.get(self.tipo)
        if extremos:
            procesos = (
                Ticket.objects.get(pk=self.origen_id).proceso,
                Ticket.objects.get(pk=self.destino_id).proceso,
            )
            if procesos != extremos:
                raise ValidationError(f"{self.tipo} une {extremos[0]} → {extremos[1]}.")


class AccionTicket(AppendOnlyModel):
    """Bitácora inmutable: sin update/delete por DomainQuerySet/AppendOnlyModel."""

    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="acciones")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    accion = models.CharField(max_length=40)
    campo = models.CharField(max_length=64, blank=True)
    valor_anterior = models.JSONField(null=True, blank=True)
    valor_nuevo = models.JSONField(null=True, blank=True)
    motivo = models.TextField(blank=True)

    class Meta:
        ordering = ["pk"]


class Visibilidad(models.TextChoices):
    PUBLICO = "PUBLICO", "Visible al solicitante"
    INTERNO = "INTERNO", "Nota interna"


class ComentarioTicket(AppendOnlyModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="comentarios")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    texto = models.TextField()
    visibilidad = models.CharField(max_length=7, choices=Visibilidad.choices)

    class Meta:
        ordering = ["pk"]

    def clean(self):
        super().clean()
        if not self.texto.strip():
            raise ValidationError({"texto": "El comentario no puede estar vacío."})


class AdjuntoTicket(AppendOnlyModel):
    identificador = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="adjuntos")
    archivo = models.FileField(storage=almacen_adjuntos, upload_to=ruta_adjunto, max_length=255)
    nombre_original = models.CharField(max_length=180)
    extension = models.CharField(max_length=8)
    tipo_mime = models.CharField(max_length=64)
    tamano = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    visibilidad = models.CharField(max_length=7, choices=Visibilidad.choices)

    class Meta:
        ordering = ["pk"]


class TransferenciaTicket(AppendOnlyModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="transferencias")
    cola_origen = models.ForeignKey(ColaServiceDesk, on_delete=models.PROTECT, related_name="+")
    cola_destino = models.ForeignKey(ColaServiceDesk, on_delete=models.PROTECT, related_name="+")
    responsable_anterior = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+",
    )
    responsable_nuevo = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+",
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    motivo = models.TextField()

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(condition=~Q(motivo=""), name="transferencia_con_motivo"),
            models.CheckConstraint(
                condition=~Q(cola_origen=F("cola_destino")), name="transferencia_colas_distintas"
            ),
        ]


class Notificacion(AppendOnlyModel):
    """Aviso interno verificable (sin correo real) de E2/E3 a la cola del incidente."""

    evento = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="avisos_emitidos")
    incidente = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="avisos")
    cola = models.ForeignKey(ColaServiceDesk, on_delete=models.PROTECT, related_name="avisos")
    mensaje = models.TextField()

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(fields=["evento", "incidente"], name="aviso_evento_uniq"),
        ]


class ReclasificacionTicket(AppendOnlyModel):
    """Cambio explícito de proceso/tipo; la transferencia nunca lo hace."""

    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="reclasificaciones")
    proceso_anterior = models.CharField(max_length=20, choices=Proceso.choices)
    proceso_nuevo = models.CharField(max_length=20, choices=Proceso.choices)
    tipo_anterior = models.CharField(max_length=20, choices=TipoTicket.choices)
    tipo_nuevo = models.CharField(max_length=20, choices=TipoTicket.choices)
    subtipo_anterior = models.CharField(max_length=18, blank=True)
    subtipo_nuevo = models.CharField(max_length=18, blank=True)
    estado_anterior = models.CharField(max_length=32)
    estado_nuevo = models.CharField(max_length=32)
    cola_anterior = models.ForeignKey(ColaServiceDesk, on_delete=models.PROTECT, related_name="+")
    cola_nueva = models.ForeignKey(ColaServiceDesk, on_delete=models.PROTECT, related_name="+")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    motivo = models.TextField()

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(condition=~Q(motivo=""), name="reclasificacion_con_motivo"),
            models.CheckConstraint(
                condition=~Q(proceso_anterior=F("proceso_nuevo")),
                name="reclasificacion_cambia_proceso",
            ),
        ]


class ArticuloConocimiento(DomainModel):
    """FAQ de nivel 0 (autoservicio); solo los publicados son visibles a todos."""

    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    categoria = models.CharField(max_length=100)
    publicado = models.BooleanField(default=False)
    servicio = models.ForeignKey(
        "catalog.ServicioNivel2", on_delete=models.PROTECT, null=True, blank=True,
        related_name="articulos",
    )
    state_field = "publicado"  # Baja lógica = despublicar.

    class Meta:
        ordering = ["categoria", "titulo"]
        verbose_name = "artículo de conocimiento"

    def __str__(self):
        return self.titulo
