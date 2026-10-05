from decimal import Decimal

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from catalog.models import ServicioNivel2
from organization.models import Area, Departamento, Empresa, Puesto, Seccion
from .web_helpers import TEST_PASSWORD, WebFixtures


class OfficialWebAcceptanceTests(WebFixtures, TestCase):
    def test_P01_login_valido_e_invalido(self):
        invalid = self.client.post(reverse("login"), {
            "username": self.admin.identificador, "password": "incorrecta-sintetica",
        })
        self.assertEqual(invalid.status_code, 200)
        self.assertContains(invalid, "Identificador o contraseña incorrectos")
        self.assertNotIn("_auth_user_id", self.client.session)
        valid = self.client.post(reverse("login"), {
            "username": " ADMIN@WEB.TEST ", "password": TEST_PASSWORD,
        })
        self.assertRedirects(valid, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.admin.pk)
        self.assertTrue(self.admin.password.startswith("argon2$argon2id$"))

    def test_P02_sin_sesion_logout_cookie_anterior_e_inactivo(self):
        self.assertRedirects(self.client.get(reverse("home")), reverse("login") + "?next=/")
        self.client.force_login(self.consulta)
        cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertTrue(Session.objects.filter(session_key=cookie).exists())
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        self.assertFalse(Session.objects.filter(session_key=cookie).exists())
        self.client.cookies[settings.SESSION_COOKIE_NAME] = cookie
        self.assertEqual(self.client.get(reverse("home")).status_code, 302)
        self.client.force_login(self.consulta)
        self.consulta.desactivar()
        self.assertEqual(self.client.get(reverse("home")).status_code, 302)
        login = self.client.post(reverse("login"), {
            "username": self.consulta.identificador, "password": TEST_PASSWORD,
        })
        self.assertEqual(login.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_P03_consulta_lee_y_no_escribe(self):
        self.client.force_login(self.consulta)
        listing = self.client.get(reverse("entity-list", kwargs={"entity": "servicios"}))
        self.assertContains(listing, self.servicio.codigo)
        self.assertNotContains(listing, "Crear registro")
        self.assertContains(self.client.get(reverse("service-detail", args=[self.servicio.pk])), self.servicio.nombre)
        requests = [
            ("entity-create", {"entity": "empresas"}, {"codigo": "ILEGAL", "nombre": "No permitido"}),
            ("entity-edit", {"entity": "servicios", "pk": self.servicio.pk}, self.service_data()),
            ("entity-deactivate", {"entity": "usuarios", "pk": self.admin.pk}, {}),
        ]
        for name, kwargs, data in requests:
            with self.subTest(operation=name):
                self.assertEqual(self.client.post(reverse(name, kwargs=kwargs), data).status_code, 403)
        self.assertFalse(Empresa.objects.filter(codigo="ILEGAL").exists())
        self.servicio.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.servicio.codigo, "WEB.1.1")
        self.assertTrue(self.admin.is_active)

    def test_P04_jerarquia_completa_y_usuario_por_http(self):
        self.client.force_login(self.admin)
        parent = None
        for slug, model, relation in (
            ("empresas", Empresa, None), ("areas", Area, "empresa"),
            ("departamentos", Departamento, "area"), ("secciones", Seccion, "departamento"),
            ("puestos", Puesto, "seccion"),
        ):
            data = {"codigo": "P04", "nombre": "Jerarquía P04", "estado": "on"}
            if relation:
                data[relation] = parent.pk
            response = self.client.post(reverse("entity-create", kwargs={"entity": slug}), data)
            self.assertEqual(response.status_code, 302)
            parent = model.objects.get(codigo="P04")
        created = self.client.post(reverse("entity-create", kwargs={"entity": "usuarios"}), {
            "identificador": "nuevo@p04.test", "nombre": "Usuario P04", "rol": "CONSULTA",
            "is_active": "on", "puesto": parent.pk,
            "nueva_password": TEST_PASSWORD, "confirmar_password": TEST_PASSWORD,
        })
        self.assertEqual(created.status_code, 302)
        user = Usuario.objects.get(identificador="nuevo@p04.test")
        self.assertEqual(user.puesto_id, parent.pk)
        self.assertEqual(user.empresa.codigo, "P04")
        self.assertTrue(user.check_password(TEST_PASSWORD))
        self.assertContains(self.client.get(reverse("entity-list", kwargs={"entity": "usuarios"})), user.identificador)

    def test_P05_duplicado_y_referencia_inexistente_rechazados(self):
        self.client.force_login(self.admin)
        duplicate = self.client.post(reverse("entity-create", kwargs={"entity": "empresas"}), {
            "codigo": self.empresa.codigo, "nombre": "Duplicada", "estado": "on",
        })
        self.assertEqual(duplicate.status_code, 200)
        self.assertTrue(duplicate.context["form"].errors)
        self.assertContains(duplicate, "Ya existe")
        self.assertEqual(Empresa.objects.filter(codigo="WEB").count(), 1)
        invalid = self.client.post(reverse("entity-create", kwargs={"entity": "areas"}), {
            "codigo": "INVALIDA", "nombre": "Inválida", "estado": "on", "empresa": 999999,
        })
        self.assertContains(invalid, "Selecciona una referencia existente y activa")
        self.assertFalse(Area.objects.filter(codigo="INVALIDA").exists())

    def test_P09_crear_y_editar_umbrales_invalidos(self):
        self.client.force_login(self.admin)
        create = self.client.post(reverse("entity-create", kwargs={"entity": "servicios"}),
                                  self.service_data(minimo="10", maximo="1"))
        self.assertContains(create, "El mínimo no puede superar al máximo")
        self.assertFalse(ServicioNivel2.objects.filter(codigo="WEB.NUEVO").exists())
        edit = self.client.post(reverse("entity-edit", kwargs={"entity": "servicios", "pk": self.servicio.pk}),
                                self.service_data(codigo=self.servicio.codigo, minimo="11", maximo="10"))
        self.assertContains(edit, "El mínimo no puede superar al máximo")
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.minimo, Decimal("0"))

    def test_P10_busqueda_filtros_combinaciones_y_paginacion(self):
        self.client.force_login(self.consulta)
        url = reverse("entity-list", kwargs={"entity": "servicios"})
        for query in (
            {"q": "web.1.1"}, {"q": "operativo"}, {"nivel1": self.n1.pk},
            {"estado": "activo"}, {"clase": self.clase.pk},
            {"criticidad": self.criticidad.pk}, {"tipo": self.tipo.pk},
            {"q": "análisis", "nivel1": self.n1.pk, "estado": "activo",
             "clase": self.clase.pk, "criticidad": self.criticidad.pk, "tipo": self.tipo.pk},
        ):
            with self.subTest(query=query):
                response = self.client.get(url, query)
                self.assertEqual(response.context["page"].paginator.count, 1)
                self.assertContains(response, self.servicio.codigo)
                self.assertNotContains(response, self.desconocido.codigo)
        unknown = self.client.get(url, {"estado": "desconocido"})
        self.assertContains(unknown, self.desconocido.codigo)
        self.assertNotContains(unknown, self.servicio.codigo)
        inactive = ServicioNivel2.objects.create(codigo="INACTIVO", nombre="Histórico", nivel1=self.n1,
                                                seccion_responsable=self.seccion, activo=False)
        self.assertContains(self.client.get(url, {"estado": "inactivo"}), inactive.codigo)
        for index in range(21):
            ServicioNivel2.objects.create(codigo=f"PAGE{index:02}", nombre="Página", nivel1=self.n1,
                                          seccion_responsable=self.seccion)
        first = self.client.get(url, {"q": "Página"})
        second = self.client.get(url, {"q": "Página", "page": 2})
        self.assertEqual(len(first.context["rows"]), 20)
        self.assertEqual(len(second.context["rows"]), 1)
        self.assertContains(first, "q=P%C3%A1gina&amp;page=2")

    def test_P11_responsable_otra_seccion_rechazado(self):
        self.client.force_login(self.admin)
        url = reverse("entity-create", kwargs={"entity": "servicios"})
        invalid = self.client.post(url, self.service_data(usuario_responsable=self.otro.pk))
        self.assertContains(invalid, "El responsable debe pertenecer a la sección del servicio")
        self.assertFalse(ServicioNivel2.objects.filter(codigo="WEB.NUEVO").exists())
        valid = self.client.post(url, self.service_data(usuario_responsable=self.consulta.pk))
        self.assertEqual(valid.status_code, 302)
        service = ServicioNivel2.objects.get(codigo="WEB.NUEVO")
        self.assertEqual(service.usuario_responsable.seccion.pk, service.seccion_responsable_id)
