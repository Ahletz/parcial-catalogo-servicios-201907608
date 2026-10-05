"""Demo local, idempotente y sin rotación silenciosa de datos humanos."""

import json
import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Usuario, normalize_identifier
from catalog.models import ServicioNivel2
from config.domain import domain_transaction
from organization.models import Area, Departamento, Empresa, Puesto, Seccion


def required_demo(name):
    value = os.environ.get(name)
    if not value or value == "CONFIGURAR_LOCALMENTE":
        raise CommandError(f"Configura {name} localmente antes de ejecutar seed_demo.")
    return value


class Command(BaseCommand):
    help = "Crea jerarquía, dos roles y tres asignaciones demo sin mostrar credenciales."

    def handle(self, *args, **options):
        credentials = [
            (normalize_identifier(required_demo("DEMO_ADMIN_IDENTIFICADOR")),
             required_demo("DEMO_ADMIN_PASSWORD"), Usuario.Rol.ADMINISTRADOR,
             "Administrador demo"),
            (normalize_identifier(required_demo("DEMO_CONSULTA_IDENTIFICADOR")),
             required_demo("DEMO_CONSULTA_PASSWORD"), Usuario.Rol.CONSULTA, "Consulta demo"),
        ]
        if not credentials[0][0] or not credentials[1][0] or credentials[0][0] == credentials[1][0]:
            raise CommandError("Los identificadores demo deben ser distintos y no vacíos.")
        try:
            with domain_transaction():
                structure_created = 0
                parent = None
                nodes = (
                    (Empresa, None, "Empresa demo"), (Area, "empresa", "Área demo"),
                    (Departamento, "area", "Departamento demo"),
                    (Seccion, "departamento", "Sección demo"),
                    (Puesto, "seccion", "Puesto demo"),
                )
                section = None
                for model, relation, name in nodes:
                    lookup = {"codigo": "DEMO"}
                    if relation:
                        lookup[relation] = parent
                    parent, created = model.objects.get_or_create(
                        **lookup, defaults={"nombre": name}
                    )
                    if not parent.estado:
                        raise CommandError("La estructura demo está inactiva; revísala antes de repetir.")
                    structure_created += int(created)
                    if model is Seccion:
                        section = parent
                users, users_created = [], 0
                for identifier, password, role, name in credentials:
                    user = Usuario.objects.filter(identificador=identifier).first()
                    if user is None:
                        candidate = Usuario(identificador=identifier, nombre=name, rol=role, puesto=parent)
                        validate_password(password, candidate)
                        user = Usuario.objects.create_user(identifier, name, parent, password, rol=role)
                        users_created += 1
                    elif not user.is_active or user.rol != role or user.puesto_id != parent.pk:
                        raise CommandError("Una cuenta demo existente tiene estado, rol o puesto diferente; revísala.")
                    users.append(user)
                assigned = ServicioNivel2.objects.filter(
                    seccion_responsable=section, usuario_responsable__in=users
                ).exclude(activo=False).count()
                needed = max(0, 3 - assigned)
                candidates = list(ServicioNivel2.objects.filter(
                    origen=ServicioNivel2.Origen.IMPORTADO,
                    seccion_responsable__isnull=True, usuario_responsable__isnull=True,
                ).exclude(activo=False).order_by("codigo")[:needed])
                if len(candidates) != needed:
                    raise CommandError("Faltan servicios disponibles: importa primero CatalogoServicios.xlsx.")
                for index, service in enumerate(candidates):
                    service.seccion_responsable = section
                    service.usuario_responsable = users[index % 2]
                    service.save()
                result = {
                    "estructura_creada": structure_created, "usuarios_creados": users_created,
                    "asignaciones_creadas": needed, "asignaciones_validas": assigned + needed,
                    "usuarios": [{"identificador": user.identificador, "rol": user.rol} for user in users],
                }
        except ValidationError as error:
            raise CommandError("Datos demo inválidos: " + "; ".join(error.messages)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))
