from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from catalog.models import ClaseServicio, CriticidadServicio, ServicioNivel1, ServicioNivel2, TipoServicio
from organization.models import Area, Departamento, Empresa, Puesto, Seccion
from .web_helpers import TEST_PASSWORD, WebFixtures


class WebMaintenanceTests(WebFixtures, TestCase):
    def test_n1_y_tres_catalogos_crear_editar_desactivar(self):
        self.client.force_login(self.admin)
        for slug, model, identity in (
            ("nivel1", ServicioNivel1, "codigo"), ("clases", ClaseServicio, "etiqueta"),
            ("criticidades", CriticidadServicio, "etiqueta"), ("tipos", TipoServicio, "etiqueta"),
        ):
            with self.subTest(entity=slug):
                data = {identity: "FUNCIONAL", "estado": "on"}
                if identity == "codigo":
                    data["nombre"] = "Grupo funcional"
                created = self.client.post(reverse("entity-create", kwargs={"entity": slug}), data)
                self.assertEqual(created.status_code, 302)
                obj = model.objects.get(**{identity: "FUNCIONAL"})
                data[identity] = "EDITADO"
                edited = self.client.post(reverse("entity-edit", kwargs={"entity": slug, "pk": obj.pk}), data)
                self.assertEqual(edited.status_code, 302)
                obj.refresh_from_db()
                self.assertEqual(getattr(obj, identity), "EDITADO")
                self.assertEqual(self.client.post(reverse("entity-deactivate", kwargs={"entity": slug, "pk": obj.pk})).status_code, 302)
                obj.refresh_from_db()
                self.assertFalse(obj.estado)
                self.assertTrue(model.objects.filter(pk=obj.pk).exists())

    def test_organizacion_y_usuario_editar_y_bajas_logicas_completas(self):
        self.client.force_login(self.admin)
        parent, created = None, []
        for slug, model, relation in (
            ("empresas", Empresa, None), ("areas", Area, "empresa"),
            ("departamentos", Departamento, "area"), ("secciones", Seccion, "departamento"),
            ("puestos", Puesto, "seccion"),
        ):
            data = {"codigo": "MANT", "nombre": "Mantenimiento", "estado": "on"}
            if relation:
                data[relation] = parent.pk
            self.assertEqual(self.client.post(reverse("entity-create", kwargs={"entity": slug}), data).status_code, 302)
            parent = model.objects.get(codigo="MANT")
            data["nombre"] = "Nombre editado"
            self.assertEqual(self.client.post(reverse("entity-edit", kwargs={"entity": slug, "pk": parent.pk}), data).status_code, 302)
            parent.refresh_from_db()
            self.assertEqual(parent.nombre, "Nombre editado")
            created.append((slug, parent))
        user_data = {"identificador": "mantenimiento@web.test", "nombre": "Mantenimiento", "puesto": parent.pk,
                     "rol": "CONSULTA", "is_active": "on", "nueva_password": TEST_PASSWORD,
                     "confirmar_password": TEST_PASSWORD}
        self.assertEqual(self.client.post(reverse("entity-create", kwargs={"entity": "usuarios"}), user_data).status_code, 302)
        user = Usuario.objects.get(identificador=user_data["identificador"])
        created.append(("usuarios", user))
        for slug, obj in reversed(created):
            self.assertEqual(self.client.post(reverse("entity-deactivate", kwargs={"entity": slug, "pk": obj.pk})).status_code, 302)
            obj.refresh_from_db()
            self.assertFalse(getattr(obj, obj.state_field))
            self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())

    def test_n2_crear_editar_desactivar_con_texto_exacto(self):
        self.client.force_login(self.admin)
        data = self.service_data(descripcion="Texto original con espacio ", tipo=self.tipo.pk, minimo="0")
        self.assertEqual(self.client.post(reverse("entity-create", kwargs={"entity": "servicios"}), data).status_code, 302)
        obj = ServicioNivel2.objects.get(codigo=data["codigo"])
        data.update(nombre="Nombre editado", usuario_responsable=self.consulta.pk)
        self.assertEqual(self.client.post(reverse("entity-edit", kwargs={"entity": "servicios", "pk": obj.pk}), data).status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.descripcion, "Texto original con espacio ")
        self.assertEqual(obj.nombre, "Nombre editado")
        self.assertEqual(obj.usuario_responsable_id, self.consulta.pk)
        self.assertEqual(self.client.post(reverse("entity-deactivate", kwargs={"entity": "servicios", "pk": obj.pk})).status_code, 302)
        obj.refresh_from_db()
        self.assertFalse(obj.activo)
        self.assertTrue(ServicioNivel2.objects.filter(pk=obj.pk).exists())

    def test_traslados_no_invalidan_responsables_por_http(self):
        self.client.force_login(self.admin)
        self.servicio.usuario_responsable = self.consulta
        self.servicio.save()
        moved = self.client.post(reverse("entity-edit", kwargs={"entity": "usuarios", "pk": self.consulta.pk}), {
            "identificador": self.consulta.identificador, "nombre": self.consulta.nombre, "rol": "CONSULTA",
            "is_active": "on", "puesto": self.otro_puesto.pk, "nueva_password": "", "confirmar_password": "",
        })
        self.assertContains(moved, "El traslado invalida responsables")
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.puesto_id, self.puesto.pk)
        position = self.client.post(reverse("entity-edit", kwargs={"entity": "puestos", "pk": self.puesto.pk}), {
            "codigo": self.puesto.codigo, "nombre": self.puesto.nombre, "estado": "on", "seccion": self.otra_seccion.pk,
        })
        self.assertContains(position, "El traslado invalida responsables")
        self.puesto.refresh_from_db()
        self.assertEqual(self.puesto.seccion_id, self.seccion.pk)

    def test_unicidad_por_padre_y_otra_empresa_por_http(self):
        self.client.force_login(self.admin)
        url = reverse("entity-create", kwargs={"entity": "areas"})
        duplicate = self.client.post(url, {"codigo": self.area.codigo, "nombre": "Duplicada",
                                           "estado": "on", "empresa": self.empresa.pk})
        self.assertEqual(duplicate.status_code, 200)
        self.assertTrue(duplicate.context["form"].non_field_errors())
        other = Empresa.objects.create(codigo="OTRAEMP", nombre="Otra")
        valid = self.client.post(url, {"codigo": self.area.codigo, "nombre": "Válida",
                                      "estado": "on", "empresa": other.pk})
        self.assertEqual(valid.status_code, 302)
        self.assertEqual(Area.objects.filter(codigo=self.area.codigo).count(), 2)
