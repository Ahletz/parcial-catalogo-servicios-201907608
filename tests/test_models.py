"""Pruebas internas de dominio/BD: no son las pruebas de aceptación P01–P12."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from accounts.models import Usuario
from catalog.models import (
    ClaseServicio, CriticidadServicio, ServicioNivel1, ServicioNivel2, TipoServicio,
)
from imports.models import EjecucionImportacion, IncidenciaImportacion, RegistroOrigen
from organization.models import Area, Departamento, Empresa, Puesto, Seccion


class ModelIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empresa = Empresa.objects.create(codigo="E1", nombre="Empresa sintética 1")
        cls.otra_empresa = Empresa.objects.create(codigo="E2", nombre="Empresa sintética 2")
        cls.area = Area.objects.create(codigo="A1", nombre="Área 1", empresa=cls.empresa)
        cls.otra_area = Area.objects.create(codigo="A1", nombre="Área 2", empresa=cls.otra_empresa)
        cls.departamento = Departamento.objects.create(codigo="D1", nombre="Departamento 1", area=cls.area)
        cls.otro_departamento = Departamento.objects.create(codigo="D1", nombre="Departamento 2", area=cls.otra_area)
        cls.seccion = Seccion.objects.create(codigo="S1", nombre="Sección 1", departamento=cls.departamento)
        cls.otra_seccion = Seccion.objects.create(codigo="S1", nombre="Sección 2", departamento=cls.otro_departamento)
        cls.puesto = Puesto.objects.create(codigo="P1", nombre="Puesto 1", seccion=cls.seccion)
        cls.otro_puesto = Puesto.objects.create(codigo="P1", nombre="Puesto 2", seccion=cls.otra_seccion)
        cls.usuario = Usuario.objects.create_user(
            "ana@example.test", "Ana sintética", cls.puesto, "solo-datos-sinteticos"
        )
        cls.otro_usuario = Usuario.objects.create_user(
            "otro", "Usuario sintético", cls.otro_puesto, "solo-datos-sinteticos"
        )
        cls.nivel1 = ServicioNivel1.objects.create(codigo="SE.TEST", nombre="Grupo sintético")
        cls.clase = ClaseServicio.objects.create(etiqueta="A DEMANDA")
        cls.criticidad = CriticidadServicio.objects.create(etiqueta="Normal")
        cls.tipo = TipoServicio.objects.create(etiqueta="Demostration")

    def service(self, **changes):
        values = {
            "codigo": "SE.TEST.1", "nombre": "Servicio sintético",
            "nivel1": self.nivel1, "seccion_responsable": self.seccion,
            "activo": True,
        }
        values.update(changes)
        return ServicioNivel2.objects.create(**values)

    def assert_database_rejects(self, instance, constraint=None, **save_kwargs):
        with self.assertRaises(IntegrityError) as captured:
            with transaction.atomic():
                # Bypass deliberado SOLO en BD test_ para comprobar constraints SQL.
                instance.save_base(**save_kwargs)
                # PostgreSQL difiere FK: verificarlas antes del rollback del test.
                connection.check_constraints()
        if constraint:
            self.assertEqual(captured.exception.__cause__.diag.constraint_name, constraint)

    def test_empresa_codigo_duplicado_rechazado(self):
        with self.assertRaises(ValidationError):
            Empresa.objects.create(codigo="E1", nombre="Duplicada")

    def test_area_codigo_duplicado_mismo_padre_rechazado(self):
        with self.assertRaises(ValidationError):
            Area.objects.create(codigo="A1", nombre="Duplicada", empresa=self.empresa)

    def test_area_codigo_mismo_otro_padre_permitido(self):
        self.assertEqual(self.area.codigo, self.otra_area.codigo)
        self.assertNotEqual(self.area.empresa_id, self.otra_area.empresa_id)

    def test_codigos_subordinados_rechazados_en_cada_padre(self):
        cases = [
            (Departamento, {"area": self.area}),
            (Seccion, {"departamento": self.departamento}),
            (Puesto, {"seccion": self.seccion}),
        ]
        for model, parent in cases:
            with self.subTest(model=model.__name__), self.assertRaises(ValidationError):
                model.objects.create(codigo=model.objects.first().codigo, nombre="Duplicado", **parent)

    def test_departamento_sin_area_rechazado(self):
        with self.assertRaises(ValidationError):
            Departamento.objects.create(codigo="N", nombre="Sin área")

    def test_seccion_sin_departamento_rechazada(self):
        with self.assertRaises(ValidationError):
            Seccion.objects.create(codigo="N", nombre="Sin departamento")

    def test_puesto_sin_seccion_rechazado(self):
        with self.assertRaises(ValidationError):
            Puesto.objects.create(codigo="N", nombre="Sin sección")

    def test_usuario_sin_puesto_rechazado(self):
        with self.assertRaises(ValidationError):
            Usuario.objects.create_user("sinpuesto", "Sin puesto", None)

    def test_empresa_usuario_derivada_sin_columna_redundante(self):
        user = Usuario.objects.get(pk=self.usuario.pk)
        self.assertEqual(user.empresa.pk, self.empresa.pk)
        self.assertNotIn("empresa", {f.name for f in Usuario._meta.fields})

    def test_varios_usuarios_por_puesto(self):
        Usuario.objects.create_user("segundo", "Segundo", self.puesto)
        self.assertEqual(self.puesto.usuarios.count(), 2)

    def test_identificador_normalizado_y_busqueda_natural(self):
        user = Usuario.objects.create_user("  MIXTO@EXAMPLE.TEST ", "Mixto", self.puesto)
        self.assertEqual(user.identificador, "mixto@example.test")
        self.assertEqual(Usuario.objects.get_by_natural_key(" MIXTO@EXAMPLE.TEST ").pk, user.pk)

    def test_identificador_duplicado_mayusculas_rechazado(self):
        with self.assertRaises(ValidationError):
            Usuario.objects.create_user("ANA@EXAMPLE.TEST", "Duplicada", self.puesto)

    def test_save_directo_normaliza_identificador_antes_de_validar(self):
        user = Usuario(
            identificador="  DIRECTO@EXAMPLE.TEST ", nombre="Directo", puesto=self.puesto
        )
        user.set_unusable_password()
        user.save()
        self.assertEqual(user.identificador, "directo@example.test")

    def test_password_argon2id_y_verificacion_sin_exponer_hash(self):
        self.assertTrue(self.usuario.password.startswith("argon2$argon2id$"))
        self.assertTrue(self.usuario.check_password("solo-datos-sinteticos"))

    def test_password_en_texto_plano_rechazado(self):
        with self.assertRaises(ValidationError):
            Usuario.objects.create(
                identificador="plano", nombre="Inválido", puesto=self.puesto,
                password="dato-sintetico-sin-hash",
            )

    def test_rol_desconocido_rechazado(self):
        with self.assertRaises(ValidationError):
            Usuario.objects.create_user("rolmalo", "Inválido", self.puesto, rol="OTRO")

    def test_superusuario_tambien_requiere_puesto(self):
        with self.assertRaises(ValidationError):
            Usuario.objects.create_superuser("super", "Super", None)

    def test_servicio_n2_sin_n1_rechazado(self):
        with self.assertRaises(ValidationError):
            self.service(nivel1=None)

    def test_codigos_servicio_duplicados_rechazados(self):
        self.service()
        with self.assertRaises(ValidationError):
            self.service()
        with self.assertRaises(ValidationError):
            ServicioNivel1.objects.create(codigo="SE.TEST", nombre="Duplicado")

    def test_minimo_mayor_maximo_creacion_rechazado(self):
        with self.assertRaises(ValidationError):
            self.service(minimo=10, maximo=1)

    def test_minimo_mayor_maximo_edicion_rechazado(self):
        service = self.service(minimo=1, maximo=2)
        service.minimo = Decimal("3")
        with self.assertRaises(ValidationError):
            service.save()
        service.refresh_from_db()
        self.assertEqual(service.minimo, Decimal("1"))

    def test_umbrales_null_permitidos_y_conservados(self):
        for index, values in enumerate(((None, None), (None, 2), (1, None))):
            with self.subTest(values=values):
                service = self.service(codigo=f"N{index}", minimo=values[0], maximo=values[1])
                service.refresh_from_db()
                self.assertEqual(service.minimo, values[0])
                self.assertEqual(service.maximo, values[1])

    def test_umbrales_iguales_permitidos(self):
        self.service(minimo=2, maximo=2)

    def test_responsable_misma_seccion_aceptado(self):
        service = self.service(usuario_responsable=self.usuario)
        self.assertEqual(service.usuario_responsable_id, self.usuario.pk)

    def test_responsable_otra_seccion_rechazado(self):
        with self.assertRaises(ValidationError):
            self.service(usuario_responsable=self.otro_usuario)

    def test_responsable_sin_seccion_rechazado(self):
        with self.assertRaises(ValidationError):
            self.service(
                origen="IMPORTADO", seccion_responsable=None,
                usuario_responsable=self.usuario,
            )

    def test_importado_sin_asignacion_y_activo_desconocido_permitido(self):
        service = self.service(origen="IMPORTADO", seccion_responsable=None, activo=None)
        service.refresh_from_db()
        self.assertIsNone(service.activo)
        self.assertIsNone(service.seccion_responsable_id)
        for name in ("clase", "criticidad", "tipo", "descripcion", "metrica", "minimo", "maximo"):
            self.assertIsNone(getattr(service, name))

    def test_manual_sin_seccion_rechazado(self):
        with self.assertRaises(ValidationError):
            self.service(seccion_responsable=None)

    def test_etiqueta_original_preservada(self):
        self.tipo.refresh_from_db()
        self.assertEqual(self.tipo.etiqueta, "Demostration")

    def test_nuevo_codigo_textual_preservado(self):
        service = self.service(codigo="SE.12.3")
        self.assertEqual(ServicioNivel2.objects.get(pk=service.pk).codigo, "SE.12.3")

    def test_relaciones_a_padres_inactivos_rechazadas(self):
        empresa = Empresa.objects.create(codigo="EI", nombre="Inactiva", estado=False)
        area = Area.objects.create(codigo="AI", nombre="Inactiva", estado=False, empresa=self.empresa)
        departamento = Departamento.objects.create(codigo="DI", nombre="Inactivo", estado=False, area=self.area)
        seccion = Seccion.objects.create(codigo="SI", nombre="Inactiva", estado=False, departamento=self.departamento)
        puesto = Puesto.objects.create(codigo="PI", nombre="Inactivo", estado=False, seccion=self.seccion)
        n1 = ServicioNivel1.objects.create(codigo="NI", nombre="Inactivo", estado=False)
        cases = [
            lambda: Area.objects.create(codigo="N", nombre="Nuevo", empresa=empresa),
            lambda: Departamento.objects.create(codigo="N", nombre="Nuevo", area=area),
            lambda: Seccion.objects.create(codigo="N", nombre="Nuevo", departamento=departamento),
            lambda: Puesto.objects.create(codigo="N", nombre="Nuevo", seccion=seccion),
            lambda: Usuario.objects.create_user("inactivo", "Nuevo", puesto),
            lambda: self.service(nivel1=n1),
            lambda: self.service(seccion_responsable=seccion),
        ]
        for index, create in enumerate(cases):
            with self.subTest(relation=index), self.assertRaises(ValidationError):
                create()

    def test_clasificaciones_inactivas_no_asignables(self):
        cases = [
            ("clase", ClaseServicio), ("criticidad", CriticidadServicio), ("tipo", TipoServicio),
        ]
        for field, model in cases:
            inactive = model.objects.create(etiqueta="Inactiva", estado=False)
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.service(**{field: inactive})

    def test_usuario_inactivo_no_asignable(self):
        self.usuario.desactivar()
        with self.assertRaises(ValidationError):
            self.service(usuario_responsable=self.usuario)

    def test_referencia_inexistente_rechazada(self):
        with self.assertRaises(ValidationError):
            self.service(clase_id=999999)

    def test_baja_con_hijos_activos_bloqueada(self):
        with self.assertRaises(ValidationError):
            self.empresa.desactivar()
        self.empresa.refresh_from_db()
        self.assertTrue(self.empresa.estado)

    def test_baja_con_dependientes_activo_desconocido_bloqueada(self):
        self.service(activo=None, clase=self.clase)
        for obj in (self.nivel1, self.clase, self.seccion):
            with self.subTest(model=type(obj).__name__), self.assertRaises(ValidationError):
                obj.desactivar()

    def test_baja_usuario_responsable_de_servicio_operativo_bloqueada(self):
        self.service(usuario_responsable=self.usuario)
        with self.assertRaises(ValidationError):
            self.usuario.desactivar()

    def test_historicos_permanecen_y_permiten_bajas_explicitas(self):
        service = self.service(usuario_responsable=self.usuario, clase=self.clase)
        service.desactivar()
        for obj in (
            self.usuario, self.puesto, self.seccion, self.departamento,
            self.area, self.empresa, self.clase, self.nivel1,
        ):
            obj.desactivar()
        service.refresh_from_db()
        self.assertFalse(service.activo)
        self.assertEqual(service.usuario_responsable_id, self.usuario.pk)
        service.nombre = "Histórico conservado"
        service.save()  # Misma relación histórica; no es asociación nueva.

    def test_reactivar_con_padre_inactivo_rechazado(self):
        service = self.service()
        service.desactivar()
        self.nivel1.desactivar()
        service.activo = True
        with self.assertRaises(ValidationError):
            service.save()

    def test_mover_usuario_no_invalida_asignacion(self):
        self.service(usuario_responsable=self.usuario)
        self.usuario.puesto = self.otro_puesto
        with self.assertRaises(ValidationError):
            self.usuario.save()

    def test_mover_puesto_no_invalida_asignacion(self):
        self.service(usuario_responsable=self.usuario)
        self.puesto.seccion = self.otra_seccion
        with self.assertRaises(ValidationError):
            self.puesto.save()

    def test_borrado_fisico_y_escrituras_masivas_bloqueados(self):
        operations = [
            lambda: self.empresa.delete(),
            lambda: Empresa.objects.filter(pk=self.empresa.pk).delete(),
            lambda: Empresa.objects.filter(pk=self.empresa.pk).update(estado=False),
            lambda: Empresa.objects.bulk_create([Empresa(codigo="B", nombre="Bulk")]),
            lambda: Empresa.objects.bulk_update([self.empresa], ["nombre"]),
        ]
        for index, operation in enumerate(operations):
            with self.subTest(operation=index), self.assertRaises(ValidationError):
                operation()
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())

    def test_save_parcial_valida_estado_que_se_persistira(self):
        service = self.service(minimo=1, maximo=2)
        service.nombre = "Nuevo nombre"
        service.minimo = 100  # No seleccionado: no se persistirá.
        service.save(update_fields=["nombre"])
        service.refresh_from_db()
        self.assertEqual(service.minimo, Decimal("1"))
        self.assertEqual(service.nombre, "Nuevo nombre")
        service.minimo = 100
        with self.assertRaises(ValidationError):
            service.save(update_fields=["minimo"])

    def test_revision_manual_distingue_cambio_de_importacion(self):
        service = self.service()
        original = service.revision_manual
        service.nombre = "Edición humana"
        service.save()
        self.assertEqual(service.revision_manual, original + 1)
        service.save()
        self.assertEqual(service.revision_manual, original + 1)
        service.metrica = "Fuente controlada"
        service.save(source="IMPORTACION")
        self.assertEqual(service.revision_manual, original + 1)

    def test_constraint_sql_empresa_unica(self):
        self.assert_database_rejects(Empresa(codigo="E1", nombre="Duplicada"))

    def test_constraint_sql_area_unica_por_padre(self):
        self.assert_database_rejects(
            Area(codigo="A1", nombre="Duplicada", empresa=self.empresa),
            "area_empresa_codigo_uniq",
        )

    def test_constraint_sql_not_null_padre(self):
        self.assert_database_rejects(Departamento(codigo="N", nombre="Huérfano"))

    def test_constraint_sql_fk_inexistente(self):
        self.assert_database_rejects(Area(codigo="N", nombre="Inválida", empresa_id=999999))

    def test_constraint_sql_umbrales(self):
        service = self.service(minimo=1, maximo=2)
        service.minimo = 3
        self.assert_database_rejects(service, "servicio_umbrales_ordenados", update_fields=["minimo"])

    def test_constraint_sql_usuario_requiere_seccion(self):
        service = self.service(origen="IMPORTADO", usuario_responsable=self.usuario)
        service.seccion_responsable = None
        self.assert_database_rejects(
            service, "servicio_usuario_requiere_seccion", update_fields=["seccion_responsable"]
        )

    def test_constraint_sql_manual_requiere_seccion(self):
        service = self.service()
        service.seccion_responsable = None
        self.assert_database_rejects(
            service, "servicio_manual_requiere_seccion", update_fields=["seccion_responsable"]
        )

    def test_constraint_sql_origen_valido(self):
        service = self.service()
        service.origen = "INVENTADO"
        self.assert_database_rejects(service, "servicio_origen_valido", update_fields=["origen"])

    def test_constraint_sql_identificador_sin_mayusculas(self):
        user = Usuario(identificador="ANA@EXAMPLE.TEST", nombre="Duplicada", puesto=self.puesto)
        user.set_unusable_password()
        self.assert_database_rejects(user, "usuario_identificador_ci_uniq")

    def test_constraint_sql_rol(self):
        self.usuario.rol = "OTRO"
        self.assert_database_rejects(self.usuario, "usuario_rol_valido", update_fields=["rol"])


class ImportTraceModelsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ejecucion = EjecucionImportacion.objects.create(
            archivo="fuente-sintetica.xlsx", sha256="a" * 64, hoja="Hoja sintética"
        )
        cls.n1 = ServicioNivel1.objects.create(codigo="SE.12", nombre="Fuente sintética")
        cls.n2 = ServicioNivel2.objects.create(
            codigo="SE.12.3", nombre="Servicio sintético", nivel1=cls.n1, origen="IMPORTADO"
        )
        cls.record = RegistroOrigen.objects.create(
            ejecucion=cls.ejecucion, entidad="NIVEL2", codigo="SE.12.3", servicio_n2=cls.n2,
            hoja="Hoja sintética", filas=[101], celdas=["C101"], rangos=[],
            valores_originales={"C101": "SE.12.3"},
            valores_importados={"nombre": "Servicio sintético", "activo": None},
            valores_aplicados={"nombre": "Servicio sintético", "activo": None},
            transformaciones=[{"regla": "prefijo exacto y único", "padre": "SE.12"}],
            revision_manual_capturada=cls.n2.revision_manual, resultado="CREADO",
        )

    def test_origen_separado_conserva_snapshot_tras_edicion(self):
        self.n2.nombre = "Edición posterior"
        self.n2.save()
        record = RegistroOrigen.objects.get(pk=self.record.pk)
        self.assertEqual(record.valores_importados["nombre"], "Servicio sintético")
        self.assertIsNone(record.valores_importados["activo"])
        self.assertEqual(record.filas, [101])

    def test_origen_inmutable(self):
        self.record.valores_originales = {"C101": "ALTERADO"}
        with self.assertRaises(ValidationError):
            self.record.save()

    def test_origen_codigo_historico_sigue_valido_tras_cambio_del_servicio(self):
        self.n2.codigo = "CODIGO.NUEVO"
        self.n2.save()
        self.record.full_clean()
        self.assertEqual(self.record.codigo, "SE.12.3")

    def test_incidencia_guarda_regla_resultado_y_ubicacion(self):
        incidence = IncidenciaImportacion.objects.create(
            ejecucion=self.ejecucion, registro=self.record, tipo="INFERENCIA",
            entidad="NIVEL2", codigo="SE.12.3", hoja="Hoja sintética",
            filas=[101], celdas=["C101"], regla_aplicada="prefijo exacto y único",
            valores={"padre_original": None}, resultado={"padre": "SE.12"},
        )
        incidence.refresh_from_db()
        self.assertEqual(incidence.resultado["padre"], "SE.12")
        self.assertIsNone(incidence.valores["padre_original"])

    def test_incidencia_no_puede_mezclar_ejecuciones(self):
        other = EjecucionImportacion.objects.create(
            archivo="otra.xlsx", sha256="b" * 64, hoja="Hoja sintética"
        )
        with self.assertRaises(ValidationError):
            IncidenciaImportacion.objects.create(
                ejecucion=other, registro=self.record, tipo="CONFLICTO",
                hoja="Hoja sintética", regla_aplicada="Regla controlada",
            )

    def test_hash_y_contadores_invalidos_rechazados(self):
        for changes in ({"sha256": "invalido"}, {"creados": -1}):
            values = {"sha256": "a" * 64, **changes}
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                EjecucionImportacion.objects.create(
                    archivo="sintetica.xlsx", hoja="Hoja sintética", **values
                )

    def test_coordenadas_invalidas_rechazadas(self):
        for changes in ({"filas": [0]}, {"celdas": ["NO ES CELDA"]}, {"rangos": ["A1"]}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                RegistroOrigen.objects.create(
                    ejecucion=self.ejecucion, entidad="NIVEL2", codigo="SE.12.3",
                    hoja="Hoja sintética", resultado="OBSERVADO", **changes,
                )

    def test_origen_codigo_incoherente_rechazado(self):
        with self.assertRaises(ValidationError):
            RegistroOrigen.objects.create(
                ejecucion=self.ejecucion, entidad="NIVEL2", codigo="OTRO",
                servicio_n2=self.n2, hoja="Hoja sintética", resultado="CREADO",
            )

    def test_constraint_sql_origen_no_mezcla_niveles(self):
        self.record.servicio_n1 = self.n1
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.record.save_base(update_fields=["servicio_n1"])
