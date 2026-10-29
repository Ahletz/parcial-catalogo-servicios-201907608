"""Clasificación y relaciones CMDB, independientes del organigrama."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from config.domain import DomainModel, NamedStateModel
from .attributes import validate_attributes, validate_schema


class CatalogoCMDB(NamedStateModel):
    codigo = models.CharField(max_length=64, unique=True)
    datos_origen = models.JSONField(default=dict, blank=True)

    class Meta(NamedStateModel.Meta):
        abstract = True

    def clean(self):
        super().clean()
        if not isinstance(self.datos_origen, dict):
            raise ValidationError({"datos_origen": "Usa un objeto JSON de procedencia."})


class ClasificacionCI(CatalogoCMDB):
    padre = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="hijas"
    )
    orden = models.PositiveIntegerField(default=0)
    esquema_atributos = models.JSONField(default=dict, blank=True)
    es_dispositivo = models.BooleanField(default=False)
    parent_field = "padre"

    class Meta(CatalogoCMDB.Meta):
        ordering = ["orden", "codigo"]
        constraints = [
            models.CheckConstraint(
                condition=Q(padre__isnull=True) | ~Q(pk=F("padre")),
                name="cmdb_clasificacion_no_autopadre",
            ),
        ]

    def _ancestor_ids(self):
        seen = {self.pk} if self.pk is not None else set()
        parent_id = self.padre_id
        ancestors = []
        using = self._state.db or "default"
        while parent_id is not None:
            if parent_id in seen:
                raise ValidationError({"padre": "La clasificación no permite ciclos."})
            seen.add(parent_id)
            parent = type(self).objects.using(using).filter(pk=parent_id).values(
                "pk", "padre_id"
            ).first()
            if parent is None:
                raise ValidationError({"padre": "La clasificación padre no existe."})
            ancestors.append(parent_id)
            parent_id = parent["padre_id"]
        return ancestors

    @property
    def nivel(self):
        return len(self._ancestor_ids()) + 1

    def ruta(self):
        """Raíz → nodo; la jerarquía es acíclica por validación."""
        nodos, actual = [], self
        while actual is not None:
            nodos.append(actual)
            actual = actual.padre
        return list(reversed(nodos))

    def ruta_codigos(self):
        return [nodo.codigo for nodo in self.ruta()]

    def clean(self):
        # Comprobar antes de la guarda común, que recorre la jerarquía activa.
        self._ancestor_ids()
        try:
            validate_schema(self.esquema_atributos)
        except ValidationError as error:
            raise ValidationError({"esquema_atributos": error.messages}) from error
        super().clean()
        previous = self.previous_values()
        using = self._state.db or "default"
        if previous:
            existing = CI.objects.using(using).filter(clasificacion_id=self.pk)
            if previous["es_dispositivo"] != self.es_dispositivo and existing.exists():
                raise ValidationError({
                    "es_dispositivo": "Reclasifica los CI antes de cambiar su naturaleza."
                })
            if previous["esquema_atributos"] != self.esquema_atributos:
                for attributes in existing.values_list("atributos", flat=True).iterator():
                    try:
                        validate_attributes(attributes, self.esquema_atributos)
                    except ValidationError as error:
                        raise ValidationError({
                            "esquema_atributos": "El cambio invalidaría atributos de CI existentes."
                        }) from error


class UbicacionCI(CatalogoCMDB):
    observaciones = models.TextField(blank=True)


class CI(CatalogoCMDB):
    clasificacion = models.ForeignKey(
        ClasificacionCI, on_delete=models.PROTECT, related_name="elementos"
    )
    ubicacion = models.ForeignKey(
        UbicacionCI, on_delete=models.PROTECT, related_name="elementos"
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="elementos_configuracion",
    )
    descripcion = models.TextField(null=True, blank=True)
    atributos = models.JSONField(default=dict, blank=True)
    servicios = models.ManyToManyField(
        "catalog.ServicioNivel2", through="ServicioCI",
        related_name="elementos_configuracion", blank=True,
    )
    parent_field = "clasificacion"

    class Meta(CatalogoCMDB.Meta):
        indexes = [
            models.Index(fields=["clasificacion", "estado"], name="cmdb_ci_clase_estado_idx"),
            models.Index(fields=["ubicacion", "estado"], name="cmdb_ci_ubic_estado_idx"),
        ]

    def clean(self):
        super().clean()
        for field in ("ubicacion", "responsable"):
            self.validate_active_reference(field)
        using = self._state.db or "default"
        classification = ClasificacionCI.objects.using(using).filter(
            pk=self.clasificacion_id
        ).first()
        if classification is not None:
            try:
                validate_attributes(self.atributos, classification.esquema_atributos)
            except ValidationError as error:
                raise ValidationError({"atributos": error.messages}) from error

    @property
    def es_dispositivo(self):
        return self.clasificacion.es_dispositivo


class TipoRelacionCI(CatalogoCMDB):
    dirigida = models.BooleanField(default=True)
    permite_ciclos = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        previous = self.previous_values()
        if previous and (
            previous["dirigida"] != self.dirigida
            or previous["permite_ciclos"] != self.permite_ciclos
        ):
            using = self._state.db or "default"
            if RelacionCI.objects.using(using).filter(tipo_id=self.pk).exists():
                raise ValidationError(
                    "No se cambia la semántica de un tipo con relaciones; crea otro tipo."
                )


def reachable(adjacency, origin, target):
    """Únicamente validación de ciclos; no es un recorrido público de impacto."""
    pending = [origin]
    visited = set()
    while pending:
        node = pending.pop()
        if node == target:
            return True
        if node not in visited:
            visited.add(node)
            pending.extend(adjacency.get(node, set()) - visited)
    return False


class RelacionCI(DomainModel):
    tipo = models.ForeignKey(
        TipoRelacionCI, on_delete=models.PROTECT, related_name="relaciones"
    )
    origen = models.ForeignKey(
        CI, on_delete=models.PROTECT, related_name="relaciones_salientes"
    )
    destino = models.ForeignKey(
        CI, on_delete=models.PROTECT, related_name="relaciones_entrantes"
    )
    estado = models.BooleanField(default=True)
    fecha = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True)
    state_field = "estado"

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "origen", "destino"], name="cmdb_relacion_pareja_uniq"
            ),
            models.CheckConstraint(
                condition=~Q(origen=F("destino")), name="cmdb_relacion_no_autoenlace"
            ),
        ]

    def clean(self):
        super().clean()
        for field in ("tipo", "origen", "destino"):
            self.validate_active_reference(field)
        if self.origen_id is None or self.destino_id is None:
            return  # clean_fields informa referencias obligatorias.
        if self.origen_id == self.destino_id:
            raise ValidationError({"destino": "No se permiten relaciones consigo mismo."})
        using = self._state.db or "default"
        kind = TipoRelacionCI.objects.using(using).filter(pk=self.tipo_id).first()
        if kind is None:
            return
        if not kind.dirigida and self.origen_id > self.destino_id:
            raise ValidationError({
                "origen": "En una relación no dirigida, usa el CI de menor ID como origen."
            })
        if not self.estado or kind.permite_ciclos:
            return
        adjacency = {}
        edges = RelacionCI.objects.using(using).filter(
            estado=True, tipo__permite_ciclos=False
        ).exclude(pk=self.pk).values_list("origen_id", "destino_id", "tipo__dirigida")
        for origin, target, directed in edges:
            adjacency.setdefault(origin, set()).add(target)
            if not directed:
                adjacency.setdefault(target, set()).add(origin)
        cyclic = reachable(adjacency, self.destino_id, self.origen_id)
        if not kind.dirigida:
            cyclic |= reachable(adjacency, self.origen_id, self.destino_id)
        if cyclic:
            raise ValidationError({"destino": "La relación formaría un ciclo no permitido."})


class ServicioCI(DomainModel):
    ci = models.ForeignKey(CI, on_delete=models.PROTECT, related_name="vinculos_servicio")
    servicio = models.ForeignKey(
        "catalog.ServicioNivel2", on_delete=models.PROTECT, related_name="vinculos_ci"
    )
    estado = models.BooleanField(default=True)
    fecha = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True)
    state_field = "estado"

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(fields=["ci", "servicio"], name="cmdb_ci_servicio_uniq"),
        ]

    def clean(self):
        super().clean()
        for field in ("ci", "servicio"):
            self.validate_active_reference(field)
