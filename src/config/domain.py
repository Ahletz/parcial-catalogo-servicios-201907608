"""Guardas de escritura comunes; reglas cruzadas serializadas en PostgreSQL."""

from contextlib import contextmanager

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import connections, models, router, transaction
from django.db.models import Q

DOMAIN_LOCK = 201907608


@contextmanager
def domain_transaction(using="default"):
    with transaction.atomic(using=using):
        if connections[using].vendor != "postgresql":
            raise ImproperlyConfigured("El dominio requiere PostgreSQL.")
        with connections[using].cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [DOMAIN_LOCK])
        yield


class DomainQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Usa save() para validar cada modificación del dominio.")

    def bulk_create(self, objs, **kwargs):
        raise ValidationError("La creación masiva omite reglas; usa save() por registro.")

    def bulk_update(self, objs, fields, **kwargs):
        raise ValidationError("La edición masiva omite reglas; usa save() por registro.")

    def delete(self):
        raise ValidationError("No se permite borrado físico; usa desactivar().")


class DomainValidationMixin:
    state_field = None
    parent_field = None

    def previous_values(self):
        if hasattr(self, "_validation_previous"):
            return self._validation_previous
        if self.pk is None:
            return None
        return type(self).objects.using(self._state.db or "default").filter(
            pk=self.pk
        ).values().first()

    def is_reactivation(self):
        previous = self.previous_values()
        return bool(
            previous and self.state_field
            and previous[self.state_field] is False
            and getattr(self, self.state_field) is not False
        )

    def validate_active_reference(self, field_name):
        previous = self.previous_values()
        field = self._meta.get_field(field_name)
        related_id = getattr(self, field.attname)
        if related_id is None:
            return
        if previous and previous[field.attname] == related_id and not self.is_reactivation():
            return  # Referencia histórica conservada, no asociación nueva.
        using = self._state.db or "default"
        node = field.related_model.objects.using(using).filter(pk=related_id).first()
        while node is not None:
            state_field = getattr(node, "state_field", None)
            if state_field and getattr(node, state_field) is not True:
                raise ValidationError({field_name: "El padre y su jerarquía deben estar activos."})
            parent = getattr(node, "parent_field", None)
            if not parent:
                break
            relation = node._meta.get_field(parent)
            node = relation.related_model.objects.using(using).filter(
                pk=getattr(node, relation.attname)
            ).first()

    def validate_deactivation(self):
        previous = self.previous_values()
        if not self.state_field or not previous:
            return
        if previous[self.state_field] is False or getattr(self, self.state_field) is not False:
            return
        using = self._state.db or "default"
        for relation in self._meta.related_objects:
            if not relation.one_to_many:
                continue
            state = getattr(relation.related_model, "state_field", None)
            if not state:
                continue  # Procedencia histórica no es dependencia operativa.
            dependencies = relation.related_model.objects.using(using).filter(
                **{relation.field.attname: self.pk}
            )
            if dependencies.filter(
                Q(**{state: True}) | Q(**{f"{state}__isnull": True})
            ).exists():
                raise ValidationError({
                    self.state_field: (
                        "Existen dependencias activas o desconocidas; "
                        "resuélvelas primero."
                    )
                })

    def clean(self):
        super().clean()
        if self.parent_field:
            self.validate_active_reference(self.parent_field)
        self.validate_deactivation()
        for name in ("codigo", "nombre", "etiqueta"):
            if not hasattr(self, name):
                continue
            value = getattr(self, name)
            field = self._meta.get_field(name)
            if field.blank and value in (None, ""):
                continue
            if not isinstance(value, str) or not value.strip():
                raise ValidationError({name: "Este valor es obligatorio."})

    def save(self, *args, source="MANUAL", **kwargs):
        if source not in {"MANUAL", "IMPORTACION"}:
            raise ValidationError("Origen de cambio desconocido.")
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and not update_fields:
            return
        using = kwargs.get("using") or router.db_for_write(type(self), instance=self)
        self._state.db = using
        with domain_transaction(using):
            previous = self.previous_values()
            self._validation_previous = previous
            try:
                # Validar lo que realmente se guardará, también en saves parciales.
                if previous and update_fields is not None:
                    selected = {self._meta.get_field(n).attname for n in update_fields}
                    for field in self._meta.concrete_fields:
                        if field.attname not in selected:
                            setattr(self, field.attname, previous[field.attname])
                if hasattr(self, "revision_manual"):
                    ignored = {"id", "created_at", "updated_at", "revision_manual"}
                    changed = previous is None or any(
                        getattr(self, f.attname) != previous[f.attname]
                        for f in self._meta.concrete_fields if f.name not in ignored
                    )
                    self.revision_manual = (previous or {}).get("revision_manual", 0)
                    if changed and source == "MANUAL":
                        self.revision_manual += 1
                    if update_fields is not None:
                        kwargs["update_fields"] = set(update_fields) | {
                            "revision_manual", "updated_at"
                        }
                self.full_clean()
                return super().save(*args, **kwargs)
            finally:
                del self._validation_previous

    def delete(self, *args, **kwargs):
        raise ValidationError("No se permite borrado físico; usa desactivar().")

    def desactivar(self):
        if not self.state_field:
            raise ValidationError("Esta entidad no admite baja lógica.")
        setattr(self, self.state_field, False)
        self.save()


class DomainModel(DomainValidationMixin, models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revision_manual = models.PositiveBigIntegerField(default=0, editable=False)
    objects = DomainQuerySet.as_manager()

    class Meta:
        abstract = True


class NamedStateModel(DomainModel):
    codigo = models.CharField(max_length=64)
    nombre = models.CharField(max_length=255)
    estado = models.BooleanField(default=True)
    state_field = "estado"

    class Meta:
        abstract = True
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class AppendOnlyModel(DomainModel):
    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        previous = self.previous_values()
        ignored = {"updated_at", "revision_manual"}
        if previous and any(
            getattr(self, f.attname) != previous[f.attname]
            for f in self._meta.concrete_fields if f.name not in ignored
        ):
            raise ValidationError("La evidencia es inmutable; registra una nueva entrada.")
