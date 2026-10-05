from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Usuario
from catalog.models import ServicioNivel2
from config.web import ENTITIES
from organization.models import Empresa
from .web_helpers import TEST_PASSWORD, WebFixtures


class WebSecurityTests(WebFixtures, TestCase):
    def test_sesion_inactiva_no_se_reutiliza_tras_reactivar(self):
        self.client.force_login(self.consulta)
        previous = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.consulta.desactivar()
        self.assertEqual(self.client.get(reverse("home")).status_code, 302)
        self.assertFalse(Session.objects.filter(session_key=previous).exists())
        self.consulta.is_active = True
        self.consulta.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = previous
        self.assertEqual(self.client.get(reverse("home")).status_code, 302)

    def test_todas_las_escrituras_rechazan_consulta(self):
        self.client.force_login(self.consulta)
        for slug, config in ENTITIES.items():
            instance = config.model.objects.first()
            for route in ("entity-create", "entity-edit", "entity-deactivate"):
                kwargs = {"entity": slug}
                if route != "entity-create":
                    kwargs["pk"] = instance.pk
                with self.subTest(entity=slug, route=route):
                    url = reverse(route, kwargs=kwargs)
                    self.assertEqual(self.client.get(url).status_code, 403)
                    self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_rutas_protegidas_rechazan_anonimo(self):
        urls = [reverse("home"), reverse("organization"), reverse("classifications"),
                reverse("service-detail", args=[self.servicio.pk])]
        for slug, config in ENTITIES.items():
            instance = config.model.objects.first()
            urls.extend([
                reverse("entity-list", kwargs={"entity": slug}),
                reverse("entity-create", kwargs={"entity": slug}),
                reverse("entity-edit", kwargs={"entity": slug, "pk": instance.pk}),
                reverse("entity-deactivate", kwargs={"entity": slug, "pk": instance.pk}),
            ])
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
                self.assertEqual(self.client.post(url, {}).status_code, 302)

    def test_todas_las_lecturas_y_formularios_admin_renderizan(self):
        self.client.force_login(self.admin)
        for slug, config in ENTITIES.items():
            instance = config.model.objects.first()
            for route in ("entity-list", "entity-create", "entity-edit", "entity-deactivate"):
                kwargs = {"entity": slug}
                if route in ("entity-edit", "entity-deactivate"):
                    kwargs["pk"] = instance.pk
                with self.subTest(entity=slug, route=route):
                    self.assertEqual(self.client.get(reverse(route, kwargs=kwargs)).status_code, 200)

    def test_csrf_login_escritura_y_logout(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("login"), {"username": self.admin.identificador,
                                                      "password": TEST_PASSWORD}).status_code, 403)
        client.force_login(self.admin)
        create = reverse("entity-create", kwargs={"entity": "empresas"})
        self.assertEqual(client.post(create, {"codigo": "SINCSRF", "nombre": "Inválida"}).status_code, 403)
        self.assertEqual(client.post(reverse("logout")).status_code, 403)
        client.get(create)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(create, {"codigo": "CSRF", "nombre": "Válida", "estado": "on",
                                        "csrfmiddlewaretoken": token})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Empresa.objects.filter(codigo="CSRF").exists())
        self.assertEqual(client.post(reverse("logout"), {"csrfmiddlewaretoken": token}).status_code, 302)

    def test_logout_get_no_modifica_sesion(self):
        self.client.force_login(self.consulta)
        session_key = self.client.session.session_key
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertEqual(self.client.session.session_key, session_key)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_cambio_rol_se_aplica_a_sesion_existente(self):
        self.client.force_login(self.admin)
        self.admin.rol = Usuario.Rol.CONSULTA
        self.admin.save()
        self.assertEqual(self.client.post(reverse("entity-create", kwargs={"entity": "empresas"}), {}).status_code, 403)

    def test_login_next_externo_no_redirige_fuera(self):
        response = self.client.post(reverse("login"), {
            "username": self.admin.identificador, "password": TEST_PASSWORD,
            "next": "https://externo.invalid/",
        })
        self.assertRedirects(response, reverse("home"))

    def test_consulta_sin_hash_y_textos_escapados(self):
        self.servicio.descripcion = '<script>alert("dato")</script>'
        self.servicio.save()
        self.client.force_login(self.consulta)
        users = self.client.get(reverse("entity-list", kwargs={"entity": "usuarios"}))
        self.assertNotContains(users, "argon2$")
        self.assertNotContains(users, self.admin.password)
        detail = self.client.get(reverse("service-detail", args=[self.servicio.pk]))
        self.assertContains(detail, "&lt;script&gt;")
        self.assertNotContains(detail, "<script>")

    def test_filtros_invalidos_sin_error_500(self):
        self.client.force_login(self.consulta)
        response = self.client.get(reverse("entity-list", kwargs={"entity": "servicios"}),
                                   {"nivel1": "no-numerico", "estado": "inventado"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page"].paginator.count, 0)
        self.assertTrue(response.context["filters"].errors)

    def test_get_baja_no_cambia_estado_y_post_bloquea_dependencias(self):
        self.client.force_login(self.admin)
        url = reverse("entity-deactivate", kwargs={"entity": "empresas", "pk": self.empresa.pk})
        self.assertEqual(self.client.get(url).status_code, 200)
        self.empresa.refresh_from_db()
        self.assertTrue(self.empresa.estado)
        response = self.client.post(url)
        self.assertContains(response, "Existen dependencias activas o desconocidas")
        self.empresa.refresh_from_db()
        self.assertTrue(self.empresa.estado)

    def test_editar_password_no_la_expone_y_vacio_conserva(self):
        self.client.force_login(self.admin)
        url = reverse("entity-edit", kwargs={"entity": "usuarios", "pk": self.consulta.pk})
        form = self.client.get(url)
        self.assertNotContains(form, self.consulta.password)
        self.assertNotContains(form, TEST_PASSWORD)
        original = self.consulta.password
        response = self.client.post(url, {
            "identificador": self.consulta.identificador, "nombre": "Nombre editado",
            "rol": "CONSULTA", "puesto": self.puesto.pk, "is_active": "on",
            "nueva_password": "", "confirmar_password": "",
            "is_superuser": "on", "is_staff": "on", "password": "dato-ignorado",
        })
        self.assertEqual(response.status_code, 302)
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.password, original)
        self.assertFalse(self.consulta.is_superuser)
        self.assertFalse(self.consulta.is_staff)

    def test_password_nueva_hash_y_sesion_anterior_invalidada(self):
        client = Client()
        client.force_login(self.consulta)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("entity-edit", kwargs={"entity": "usuarios", "pk": self.consulta.pk}), {
            "identificador": self.consulta.identificador, "nombre": self.consulta.nombre,
            "rol": "CONSULTA", "puesto": self.puesto.pk, "is_active": "on",
            "nueva_password": "Otra-Prueba-Sintetica-2026!",
            "confirmar_password": "Otra-Prueba-Sintetica-2026!",
        })
        self.assertEqual(response.status_code, 302)
        self.consulta.refresh_from_db()
        self.assertTrue(self.consulta.check_password("Otra-Prueba-Sintetica-2026!"))
        self.assertEqual(client.get(reverse("home")).status_code, 302)

    def test_password_corta_o_confirmacion_distinta_no_crea(self):
        self.client.force_login(self.admin)
        for first, second in (("corta", "corta"), (TEST_PASSWORD, "distinta")):
            response = self.client.post(reverse("entity-create", kwargs={"entity": "usuarios"}), {
                "identificador": "invalido@web.test", "nombre": "Inválido", "rol": "CONSULTA",
                "puesto": self.puesto.pk, "is_active": "on", "nueva_password": first,
                "confirmar_password": second,
            })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
            self.assertFalse(Usuario.objects.filter(identificador="invalido@web.test").exists())

    def test_servicio_edicion_null_cero_y_origen_interno(self):
        self.client.force_login(self.admin)
        url = reverse("entity-edit", kwargs={"entity": "servicios", "pk": self.desconocido.pk})
        response = self.client.post(url, self.service_data(
            codigo=self.desconocido.codigo, activo="", seccion_responsable="", minimo="0", origen="MANUAL",
        ))
        self.assertEqual(response.status_code, 302)
        self.desconocido.refresh_from_db()
        self.assertEqual(self.desconocido.origen, "IMPORTADO")
        self.assertIsNone(self.desconocido.activo)
        self.assertEqual(self.desconocido.minimo, 0)
        self.assertIsNone(self.desconocido.maximo)
        self.assertIsNone(self.desconocido.descripcion)
        self.assertIsNone(self.desconocido.seccion_responsable_id)

    def test_estado_actual_formulario_se_conserva(self):
        self.client.force_login(self.admin)
        for service, selected in ((self.servicio, "true"), (self.desconocido, "")):
            response = self.client.get(reverse("entity-edit", kwargs={"entity": "servicios", "pk": service.pk}))
            self.assertContains(response, f'<option value="{selected}" selected>')

    def test_ficha_todos_atributos_y_desconocidos(self):
        self.client.force_login(self.consulta)
        detail = self.client.get(reverse("service-detail", args=[self.desconocido.pk]))
        for label in ("Código", "Nombre", "Nivel 1", "Estado", "Clase", "Criticidad", "Tipo",
                      "Descripción", "Métrica", "Mínimo", "Máximo", "Sección responsable", "Usuario responsable"):
            self.assertContains(detail, label)
        self.assertContains(detail, "Desconocido")
        self.assertContains(detail, "Sin informar")

    def test_clasificaciones_controladas_y_ausencia_manual_rechazada(self):
        self.client.force_login(self.admin)
        url = reverse("entity-create", kwargs={"entity": "servicios"})
        arbitrary = self.client.post(url, self.service_data(tipo="Demostration"))
        self.assertContains(arbitrary, "Selecciona una referencia existente y activa")
        missing = self.client.post(url, self.service_data(seccion_responsable=""))
        self.assertContains(missing, "Un servicio manual requiere sección")
        self.assertFalse(ServicioNivel2.objects.filter(codigo="WEB.NUEVO").exists())

    def test_parent_inactivo_y_renombre_historico(self):
        self.client.force_login(self.admin)
        inactive = Empresa.objects.create(codigo="INACTIVA", nombre="Inactiva", estado=False)
        response = self.client.post(reverse("entity-create", kwargs={"entity": "areas"}), {
            "codigo": "NO", "nombre": "No", "estado": "on", "empresa": inactive.pk,
        })
        self.assertContains(response, "Selecciona una referencia existente y activa")
        self.desconocido.desactivar()
        self.otro_n1.desactivar()
        edit = self.client.post(reverse("entity-edit", kwargs={"entity": "servicios", "pk": self.desconocido.pk}),
                                self.service_data(codigo=self.desconocido.codigo, nivel1=self.otro_n1.pk,
                                                  activo="false", seccion_responsable=""))
        self.assertEqual(edit.status_code, 302)
