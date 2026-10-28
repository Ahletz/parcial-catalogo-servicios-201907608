import hashlib
import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from config.domain import AppendOnlyModel, DomainModel
from .catalogo import (
    Afectacion, CategoriaEvento, CategoriaIncidente, Nivel, Proceso, REFERENCIA_INCIDENTES,
    sugerir_categoria_incidente,
)
from .motor import serializar


class DetalleProceso(DomainModel):
    """Datos propios de un proceso, uno por ticket y nunca compartidos."""

    proceso = None
    campos_aprobados = ()

    ticket = models.OneToOneField(
        "service_desk.Ticket", on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        previous = self.previous_values()
        if previous and previous["ticket_id"] != self.ticket_id:
            raise ValidationError("El detalle no cambia de ticket.")
        if self.ticket_id:
            ticket_model = self._meta.get_field("ticket").related_model
            proceso = ticket_model.objects.filter(pk=self.ticket_id).values_list(
                "proceso", flat=True
            ).first()
            if proceso != self.proceso:
                raise ValidationError("El detalle no corresponde al proceso del ticket.")

    def contenido_aprobado(self):
        return {
            nombre: serializar(getattr(self, self._meta.get_field(nombre).attname))
            for nombre in self.campos_aprobados
        }

    def huella(self):
        """Resumen del contenido sometido a aprobación; cambiarlo la invalida."""
        texto = json.dumps(self.contenido_aprobado(), sort_keys=True, default=str)
        return hashlib.sha256(texto.encode()).hexdigest()


class Aprobacion(AppendOnlyModel):
    class Decision(models.TextChoices):
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"

    ticket = models.ForeignKey(
        "service_desk.Ticket", on_delete=models.PROTECT, related_name="aprobaciones"
    )
    aprobador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="aprobaciones_sd"
    )
    decision = models.CharField(max_length=9, choices=Decision.choices)
    estado_origen = models.CharField(max_length=32)
    motivo = models.TextField(blank=True)
    huella = models.CharField(max_length=64)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(decision="APROBADA") | ~Q(motivo=""),
                name="aprobacion_rechazo_con_motivo",
            ),
        ]

    def clean(self):
        super().clean()
        if self.previous_values():
            return
        ticket = self._meta.get_field("ticket").related_model.objects.get(pk=self.ticket_id)
        # Defensa en el modelo, además de la guarda del flujo.
        if self.aprobador_id in {ticket.solicitante_id, ticket.creador_id}:
            raise ValidationError("El solicitante no puede aprobar su propia solicitud.")
        if ticket.proceso == Proceso.ACCESOS:
            beneficiario = DetalleAcceso.objects.filter(ticket_id=ticket.pk).values_list(
                "beneficiario_id", flat=True
            ).first()
            if beneficiario == self.aprobador_id:
                raise ValidationError("El beneficiario no puede aprobar su propio acceso.")
        aprobador = self._meta.get_field("aprobador").related_model.objects.get(
            pk=self.aprobador_id
        )
        if not aprobador.is_active or aprobador.rol == aprobador.Rol.CONSULTA:
            raise ValidationError("El aprobador debe estar activo y no ser de consulta.")


class DetalleNuevoServicio(DetalleProceso):
    class Modo(models.TextChoices):
        CREAR = "CREAR", "Crear servicio"
        VINCULAR = "VINCULAR", "Vincular servicio existente"

    proceso = Proceso.NUEVOS_SERVICIOS
    campos_aprobados = (
        "necesidad", "viabilidad", "modo_resultado", "servicio_resultante",
        "propuesta_codigo", "propuesta_nombre", "propuesta_nivel1", "propuesta_seccion",
    )
    necesidad = models.TextField()
    viabilidad = models.TextField(blank=True)
    modo_resultado = models.CharField(max_length=8, choices=Modo.choices, blank=True)
    servicio_resultante = models.ForeignKey(
        "catalog.ServicioNivel2", on_delete=models.PROTECT, null=True, blank=True,
        related_name="solicitudes_origen",
    )
    propuesta_codigo = models.CharField(max_length=64, blank=True)
    propuesta_nombre = models.CharField(max_length=255, blank=True)
    propuesta_nivel1 = models.ForeignKey(
        "catalog.ServicioNivel1", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+",
    )
    propuesta_seccion = models.ForeignKey(
        "organization.Seccion", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+",
    )
    propuesta_descripcion = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.modo_resultado == self.Modo.VINCULAR:
            self.validate_active_reference("servicio_resultante")
        if self.modo_resultado == self.Modo.CREAR:
            for campo in ("propuesta_nivel1", "propuesta_seccion"):
                self.validate_active_reference(campo)


class DetalleCambio(DetalleProceso):
    proceso = Proceso.CAMBIOS
    campos_aprobados = ("impacto", "riesgo", "analisis_impacto", "plan_pruebas",
                        "plan_reversion")
    impacto = models.CharField(max_length=5, choices=Nivel.choices, blank=True)
    riesgo = models.CharField(max_length=5, choices=Nivel.choices, blank=True)
    analisis_impacto = models.TextField(blank=True)
    plan_pruebas = models.TextField(blank=True)
    plan_reversion = models.TextField(blank=True)
    fecha_planificada = models.DateTimeField(null=True, blank=True)
    resultado_validacion = models.TextField(blank=True)
    exitoso = models.BooleanField(null=True, blank=True)
    evidencia_reversion = models.TextField(blank=True)

    def contenido_aprobado(self):
        contenido = super().contenido_aprobado()
        # Los CI afectados forman parte de lo aprobado.
        ticket_ci = self._meta.get_field("ticket").related_model.cis.through
        contenido["cis"] = sorted(
            ticket_ci.objects.filter(ticket_id=self.ticket_id).values_list("ci_id", flat=True)
        )
        return contenido


class DetalleIncidente(DetalleProceso):
    proceso = Proceso.INCIDENTES
    afectacion = models.CharField(max_length=16, choices=Afectacion.choices, blank=True)
    categoria = models.CharField(max_length=2, choices=CategoriaIncidente.choices, blank=True)
    categoria_sugerida = models.CharField(
        max_length=2, choices=CategoriaIncidente.choices, blank=True, editable=False
    )
    motivo_categoria = models.TextField(blank=True)
    duracion_estimada = models.DurationField(null=True, blank=True)
    duracion_real = models.DurationField(null=True, blank=True)
    redundancia = models.BooleanField(null=True, blank=True)
    diagnostico = models.TextField(blank=True)
    solucion_aplicada = models.TextField(blank=True)
    nivel_escalamiento = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(nivel_escalamiento__isnull=True) | Q(nivel_escalamiento__lte=4),
                name="incidente_nivel_escalamiento_0_4",
            ),
        ]

    def clean(self):
        super().clean()
        for campo in ("duracion_estimada", "duracion_real"):
            valor = getattr(self, campo)
            if valor is not None and valor.total_seconds() < 0:
                raise ValidationError({campo: "La duración no puede ser negativa."})
        # Solo sugerencia: la categoría la elige una persona (SD-DP05).
        duracion = self.duracion_real or self.duracion_estimada
        self.categoria_sugerida = sugerir_categoria_incidente(self.afectacion, duracion) or ""

    @property
    def referencia_docente(self):
        return REFERENCIA_INCIDENTES.get(self.categoria)


class DetalleEvento(DetalleProceso):
    proceso = Proceso.EVENTOS
    clave_evento = models.CharField(max_length=128, unique=True)
    fuente = models.CharField(max_length=128, blank=True)
    categoria = models.CharField(max_length=2, choices=CategoriaEvento.choices, blank=True)
    evaluacion = models.TextField(blank=True)
    respuesta = models.TextField(blank=True)
    incidente = models.ForeignKey(
        "service_desk.Ticket", on_delete=models.PROTECT, null=True, blank=True,
        related_name="eventos_origen",
    )

    def clean(self):
        super().clean()
        previous = self.previous_values()
        if previous and previous["incidente_id"] and previous["incidente_id"] != self.incidente_id:
            raise ValidationError({"incidente": "El incidente vinculado no se reemplaza."})
        if previous and previous["clave_evento"] != self.clave_evento:
            raise ValidationError({"clave_evento": "La identidad del evento es inmutable."})
        if self.incidente_id:
            ticket_model = self._meta.get_field("incidente").related_model
            if ticket_model.objects.filter(pk=self.incidente_id).values_list(
                "proceso", flat=True
            ).first() != Proceso.INCIDENTES:
                raise ValidationError({"incidente": "Debe vincularse a un incidente."})


class DetalleProblema(DetalleProceso):
    proceso = Proceso.PROBLEMAS
    causa_raiz = models.TextField(blank=True)
    workaround = models.TextField(blank=True)
    solucion_definitiva = models.TextField(blank=True)
    justificacion_sin_cambio = models.TextField(blank=True)

    @property
    def es_error_conocido(self):
        return bool(self.causa_raiz.strip() and self.workaround.strip())


class DetalleAcceso(DetalleProceso):
    class Accion(models.TextChoices):
        PROVISION = "PROVISION", "Provisión"
        REVOCACION = "REVOCACION", "Revocación"

    proceso = Proceso.ACCESOS
    campos_aprobados = ("beneficiario", "recurso", "permiso", "accion")
    beneficiario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="accesos_sd"
    )
    recurso = models.CharField(max_length=255)
    permiso = models.CharField(max_length=255)
    accion = models.CharField(max_length=10, choices=Accion.choices)
    evidencia_ejecucion = models.TextField(blank=True)
    resultado_validacion = models.TextField(blank=True)

    def clean(self):
        super().clean()
        previous = self.previous_values()
        if previous is None or previous["beneficiario_id"] != self.beneficiario_id:
            self.validate_active_reference("beneficiario")


class DetalleServicioTecnologia(DetalleProceso):
    proceso = Proceso.SERVICIOS_TECNOLOGIA
    resultado_validacion = models.TextField(blank=True)
    detalle_cumplimiento = models.TextField(blank=True)
