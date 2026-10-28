import unicodedata

from django.apps import apps
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import identify_hasher, is_password_usable
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from config.domain import DomainQuerySet, DomainValidationMixin


def normalize_identifier(value):
    return unicodedata.normalize("NFKC", value or "").strip().casefold()


class UsuarioManager(BaseUserManager.from_queryset(DomainQuerySet)):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(identificador=normalize_identifier(username))

    def create_user(self, identificador, nombre, puesto, password=None, **extra_fields):
        user = self.model(
            identificador=normalize_identifier(identificador),
            nombre=nombre,
            **extra_fields,
        )
        if hasattr(puesto, "pk"):
            user.puesto = puesto
        else:
            user.puesto_id = puesto
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, identificador, nombre, puesto, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", "ADMINISTRADOR")
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("El superusuario requiere is_staff e is_superuser.")
        if extra_fields["rol"] != "ADMINISTRADOR":
            raise ValueError("El superusuario debe ser ADMINISTRADOR.")
        return self.create_user(identificador, nombre, puesto, password, **extra_fields)


class Usuario(DomainValidationMixin, AbstractBaseUser, PermissionsMixin):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        CONSULTA = "CONSULTA", "Consulta"
        # Sin escritura PP2; capacidades Service Desk solo por roles/colas.
        OPERATIVO = "OPERATIVO", "Operativo Service Desk"

    identificador = models.CharField(
        max_length=150, unique=True, validators=[UnicodeUsernameValidator()]
    )
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=13, choices=Rol.choices, default=Rol.CONSULTA)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    puesto = models.ForeignKey(
        "organization.Puesto", on_delete=models.PROTECT, related_name="usuarios"
    )
    objects = UsuarioManager()
    USERNAME_FIELD = "identificador"
    REQUIRED_FIELDS = ["nombre", "puesto"]
    state_field = "is_active"
    parent_field = "puesto"

    class Meta:
        ordering = ["identificador"]
        constraints = [
            models.UniqueConstraint(
                Lower("identificador"), name="usuario_identificador_ci_uniq"
            ),
            models.CheckConstraint(
                condition=Q(rol__in=["ADMINISTRADOR", "CONSULTA", "OPERATIVO"]),
                name="usuario_rol_valido",
            ),
            models.CheckConstraint(
                condition=Q(is_superuser=False) | Q(rol="ADMINISTRADOR", is_staff=True),
                name="usuario_superusuario_admin",
            ),
        ]

    @property
    def empresa(self):
        return self.puesto.seccion.departamento.area.empresa

    @property
    def seccion(self):
        return self.puesto.seccion

    def clean_fields(self, exclude=None):
        self.identificador = normalize_identifier(self.identificador)
        super().clean_fields(exclude=exclude)

    def clean(self):
        self.identificador = normalize_identifier(self.identificador)
        super().clean()
        if self.password is not None and is_password_usable(self.password):
            try:
                identify_hasher(self.password)
            except ValueError as exc:
                raise ValidationError({
                    "password": "Usa set_password(); no se admite texto plano."
                }) from exc
        previous = self.previous_values()
        if previous and previous["puesto_id"] != self.puesto_id:
            puesto_model = self._meta.get_field("puesto").related_model
            puesto = puesto_model.objects.filter(pk=self.puesto_id).first()
            service = apps.get_model("catalog", "ServicioNivel2")
            if puesto and service.objects.filter(
                usuario_responsable_id=self.pk
            ).exclude(seccion_responsable_id=puesto.seccion_id).exists():
                raise ValidationError({
                    "puesto": (
                        "El traslado invalida responsables; "
                        "resuelve sus asignaciones primero."
                    )
                })
        pierde_atencion = previous and (
            (previous["is_active"] and not self.is_active)
            or (previous["rol"] != self.Rol.CONSULTA and self.rol == self.Rol.CONSULTA)
        )
        if pierde_atencion:
            ticket = apps.get_model("service_desk", "Ticket")
            if ticket.objects.abiertos().filter(responsable_id=self.pk).exists():
                raise ValidationError({
                    "is_active": (
                        "Tiene tickets abiertos asignados; reasígnalos o "
                        "transfiérelos antes de desactivar o pasar a consulta."
                    )
                })

    def get_full_name(self):
        return self.nombre

    def get_short_name(self):
        return self.nombre

    def __str__(self):
        return self.identificador
