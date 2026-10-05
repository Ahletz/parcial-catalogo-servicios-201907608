import json
import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from accounts.models import Usuario
from catalog.models import ServicioNivel2
from organization.models import Empresa, Puesto
from .web_helpers import TEST_PASSWORD, WebFixtures


DEMO_ENV = {
    "DEMO_ADMIN_IDENTIFICADOR": "demo.admin@seed.test", "DEMO_ADMIN_PASSWORD": TEST_PASSWORD,
    "DEMO_CONSULTA_IDENTIFICADOR": "demo.consulta@seed.test", "DEMO_CONSULTA_PASSWORD": TEST_PASSWORD,
}


class SeedDemoTests(WebFixtures, TestCase):
    def seed(self):
        output = StringIO()
        call_command("seed_demo", stdout=output)
        self.assertNotIn(TEST_PASSWORD, output.getvalue())
        self.assertNotIn("argon2$", output.getvalue())
        return json.loads(output.getvalue())

    def services(self):
        return [ServicioNivel2.objects.create(
            codigo=f"SEED.{index}", nombre="Importado sintético", nivel1=self.n1, origen="IMPORTADO",
        ) for index in range(3)]

    @patch.dict(os.environ, DEMO_ENV)
    def test_demo_dos_roles_tres_asignaciones_y_repeticion(self):
        self.services()
        first = self.seed()
        self.assertEqual(first["estructura_creada"], 5)
        self.assertEqual(first["usuarios_creados"], 2)
        self.assertEqual(first["asignaciones_creadas"], 3)
        self.assertEqual(first["asignaciones_validas"], 3)
        before = (Empresa.objects.count(), Puesto.objects.count(), Usuario.objects.count(), ServicioNivel2.objects.count())
        second = self.seed()
        self.assertEqual(second["estructura_creada"], 0)
        self.assertEqual(second["usuarios_creados"], 0)
        self.assertEqual(second["asignaciones_creadas"], 0)
        self.assertEqual(before, (Empresa.objects.count(), Puesto.objects.count(), Usuario.objects.count(), ServicioNivel2.objects.count()))
        users = Usuario.objects.filter(identificador__in=[DEMO_ENV["DEMO_ADMIN_IDENTIFICADOR"], DEMO_ENV["DEMO_CONSULTA_IDENTIFICADOR"]])
        self.assertEqual(set(users.values_list("rol", flat=True)), {"ADMINISTRADOR", "CONSULTA"})
        for user in users:
            self.assertTrue(user.check_password(TEST_PASSWORD))
        for service in ServicioNivel2.objects.filter(usuario_responsable__in=users):
            self.assertEqual(service.usuario_responsable.seccion.pk, service.seccion_responsable_id)

    @patch.dict(os.environ, DEMO_ENV)
    def test_sin_servicios_rollback_demo_completo(self):
        # Solo queda un importado en fixture: insuficiente para garantizar tres.
        with self.assertRaisesMessage(CommandError, "importa primero"):
            self.seed()
        self.assertFalse(Empresa.objects.filter(codigo="DEMO").exists())
        self.assertFalse(Usuario.objects.filter(identificador=DEMO_ENV["DEMO_ADMIN_IDENTIFICADOR"]).exists())

    @patch.dict(os.environ, DEMO_ENV)
    def test_repetir_conserva_password_humana(self):
        self.services()
        self.seed()
        user = Usuario.objects.get(identificador=DEMO_ENV["DEMO_ADMIN_IDENTIFICADOR"])
        user.set_password("Password-Humana-Sintetica-2026!")
        user.save()
        self.seed()
        user.refresh_from_db()
        self.assertTrue(user.check_password("Password-Humana-Sintetica-2026!"))

    @patch.dict(os.environ, DEMO_ENV)
    def test_no_sobrescribe_asignacion_humana(self):
        imported = self.services()
        imported[0].seccion_responsable = self.seccion
        imported[0].usuario_responsable = self.consulta
        imported[0].save()
        self.seed()
        imported[0].refresh_from_db()
        self.assertEqual(imported[0].seccion_responsable_id, self.seccion.pk)
        self.assertEqual(imported[0].usuario_responsable_id, self.consulta.pk)

    @patch.dict(os.environ, DEMO_ENV)
    def test_cuenta_demo_incompatible_no_se_promueve(self):
        self.services()
        self.seed()
        user = Usuario.objects.get(identificador=DEMO_ENV["DEMO_ADMIN_IDENTIFICADOR"])
        user.rol = "CONSULTA"
        user.save()
        with self.assertRaisesMessage(CommandError, "estado, rol o puesto diferente"):
            self.seed()
        user.refresh_from_db()
        self.assertEqual(user.rol, "CONSULTA")

    @patch.dict(os.environ, DEMO_ENV)
    def test_password_placeholder_rechazada_sin_escritura(self):
        with patch.dict(os.environ, {"DEMO_ADMIN_PASSWORD": "CONFIGURAR_LOCALMENTE"}):
            with self.assertRaisesMessage(CommandError, "Configura DEMO_ADMIN_PASSWORD"):
                self.seed()
        self.assertFalse(Empresa.objects.filter(codigo="DEMO").exists())

    @patch.dict(os.environ, DEMO_ENV)
    def test_identificadores_iguales_rechazados(self):
        with patch.dict(os.environ, {"DEMO_CONSULTA_IDENTIFICADOR": DEMO_ENV["DEMO_ADMIN_IDENTIFICADOR"].upper()}):
            with self.assertRaisesMessage(CommandError, "distintos"):
                self.seed()
        self.assertFalse(Empresa.objects.filter(codigo="DEMO").exists())
