from unittest.mock import patch

from django.core.management.base import CommandError
from django.test import TestCase

from accounts.models import Usuario
from catalog.models import ClaseServicio, ServicioNivel1, ServicioNivel2, TipoServicio
from imports.models import EjecucionImportacion, IncidenciaImportacion, RegistroOrigen
from imports.services.exceptions import CatalogImportError
from imports.services.importer import import_catalog
from imports.services.traceability import write_origin
from organization.models import Area, Departamento, Empresa, Puesto, Seccion

from .import_helpers import ORIGINAL, changed_source, command_report


class ImportPersistenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.initial = import_catalog(ORIGINAL).execution

    def test_origen_persistido_con_original_interpretado_y_rangos(self):
        origin = RegistroOrigen.objects.get(
            ejecucion=self.initial, servicio_n2__codigo="SE.01.01"
        )
        self.assertIn("C5:C7", origin.rangos)
        self.assertEqual(origin.valores_originales["C6"]["principal"], "C5")
        self.assertEqual(origin.valores_originales["I5"]["valor"], "Revele su rollo ")
        self.assertEqual(origin.valores_importados["minimo"], "1")
        self.assertEqual(origin.valores_aplicados["minimo"], "1")

    def test_filas_42_y_67_incidentes_sin_vinculo_servicio(self):
        incidents = IncidenciaImportacion.objects.filter(tipo="FILA_SIN_IDENTIDAD")
        self.assertEqual(incidents.count(), 2)
        for row in (42, 67):
            incident = incidents.get(filas__contains=[row])
            self.assertIsNone(incident.registro_id)
            self.assertEqual(incident.codigo, "")
            self.assertIsNone(incident.valores["originales"][f"C{row}"]["valor"])
            self.assertEqual(incident.valores["originales"][f"E{row}"]["valor"], "S")

    def test_conflicto_se12_persistente_y_ambos_nombres(self):
        incident = IncidenciaImportacion.objects.get(tipo="CONFLICTO_N1", codigo="SE.12")
        values = {candidate["valor"] for candidate in incident.valores["candidatos"]}
        self.assertEqual(values, {"Suministrar Analitica", "Mantener Tableros de Control"})
        self.assertIn("B99", incident.celdas)
        self.assertIn("B100", incident.celdas)

    def test_inferencia_101_persistente(self):
        origin = RegistroOrigen.objects.get(servicio_n2__codigo="SE.12.3")
        self.assertIn(101, origin.filas)
        self.assertIn("C101", origin.celdas)
        self.assertTrue(any(
            transform["regla"] == "PREFIJO_EXACTO_Y_UNICO"
            for transform in origin.transformaciones
        ))
        self.assertTrue(IncidenciaImportacion.objects.filter(
            registro=origin, tipo="INFERENCIA_N1"
        ).exists())

    def test_idempotencia_entidades_y_nueva_trazabilidad(self):
        second = import_catalog(ORIGINAL).execution
        self.assertEqual((second.creados, second.actualizados, second.omitidos), (0, 0, 76))
        self.assertEqual(ServicioNivel1.objects.count(), 12)
        self.assertEqual(ServicioNivel2.objects.count(), 46)
        self.assertEqual(RegistroOrigen.objects.count(), 152)
        self.assertEqual(EjecucionImportacion.objects.count(), 2)
        self.assertEqual(IncidenciaImportacion.objects.count(), 8)

    def test_decimal_equivalente_no_produce_falsa_divergencia(self):
        second = import_catalog(ORIGINAL).execution
        self.assertFalse(second.incidencias.filter(tipo="DIVERGENCIA_HUMANA").exists())
        self.assertEqual(second.actualizados, 0)

    def test_edicion_humana_protegida_en_segunda_y_tercera_importacion(self):
        service = ServicioNivel2.objects.get(codigo="SE.01.02")
        service.nombre = "Nombre decidido por usuario"
        service.save()
        revision = service.revision_manual
        for _ in range(2):
            result = import_catalog(ORIGINAL).execution
            service.refresh_from_db()
            self.assertEqual(service.nombre, "Nombre decidido por usuario")
            self.assertEqual(service.revision_manual, revision)
            incident = result.incidencias.get(tipo="DIVERGENCIA_HUMANA")
            self.assertEqual(incident.valores["nuevo_excel"], "Suministrar Corriente Regulada")
            self.assertEqual(incident.valores["actual"], "Nombre decidido por usuario")
            origin = result.registros.get(servicio_n2=service)
            self.assertEqual(origin.valores_aplicados["nombre"], service.nombre)
            self.assertEqual(origin.valores_importados["nombre"], "Suministrar Corriente Regulada")

    def test_cambio_fuente_sin_edicion_humana_se_actualiza(self):
        with changed_source(lambda book: setattr(book.active["D8"], "value", "Fuente actualizada")) as file:
            execution = import_catalog(file).execution
            self.assertEqual(execution.actualizados, 1)
            self.assertEqual(
                ServicioNivel2.objects.get(codigo="SE.01.02").nombre, "Fuente actualizada"
            )
            repeated = import_catalog(file).execution
            self.assertEqual((repeated.creados, repeated.actualizados, repeated.omitidos), (0, 0, 76))

    def test_edicion_humana_y_nueva_fuente_divergente(self):
        service = ServicioNivel2.objects.get(codigo="SE.01.02")
        service.nombre = "Edición humana"
        service.save()
        with changed_source(lambda book: setattr(book.active["D8"], "value", "Nueva fuente")) as file:
            execution = import_catalog(file).execution
        service.refresh_from_db()
        self.assertEqual(service.nombre, "Edición humana")
        incident = execution.incidencias.get(tipo="DIVERGENCIA_HUMANA")
        self.assertEqual(incident.valores["nuevo_excel"], "Nueva fuente")

    def test_comparacion_por_campo_actualiza_otro_y_conserva_humano(self):
        service = ServicioNivel2.objects.get(codigo="SE.01.02")
        service.nombre = "Edición humana"
        service.save()
        with changed_source(lambda book: setattr(book.active["J8"], "value", "Métrica nueva")) as file:
            execution = import_catalog(file).execution
        service.refresh_from_db()
        self.assertEqual(service.nombre, "Edición humana")
        self.assertEqual(service.metrica, "Métrica nueva")
        self.assertEqual(execution.actualizados, 1)
        self.assertTrue(execution.incidencias.filter(tipo="DIVERGENCIA_HUMANA").exists())

    def test_asignaciones_organizacionales_no_se_tocan(self):
        company = Empresa.objects.create(codigo="TEST", nombre="Empresa sintética")
        area = Area.objects.create(codigo="TEST", nombre="Área", empresa=company)
        department = Departamento.objects.create(codigo="TEST", nombre="Departamento", area=area)
        section = Seccion.objects.create(codigo="TEST", nombre="Sección", departamento=department)
        job = Puesto.objects.create(codigo="TEST", nombre="Puesto", seccion=section)
        user = Usuario.objects.create_user("sintetico", "Usuario sintético", job)
        service = ServicioNivel2.objects.get(codigo="SE.01.02")
        service.seccion_responsable = section
        service.usuario_responsable = user
        service.save()
        import_catalog(ORIGINAL)
        service.refresh_from_db()
        self.assertEqual(service.seccion_responsable_id, section.pk)
        self.assertEqual(service.usuario_responsable_id, user.pk)

    def test_codigo_humano_renombrado_no_recrea_servicio_original(self):
        service = ServicioNivel2.objects.get(codigo="SE.12.3")
        service.codigo = "CODIGO.HUMANO"
        service.save()
        execution = import_catalog(ORIGINAL).execution
        self.assertEqual(ServicioNivel2.objects.count(), 46)
        self.assertFalse(ServicioNivel2.objects.filter(codigo="SE.12.3").exists())
        origin = execution.registros.get(servicio_n2=service)
        self.assertEqual(origin.codigo, "CODIGO.HUMANO")
        self.assertEqual(origin.valores_importados["codigo"], "SE.12.3")

    def test_codigo_n1_humano_renombrado_conserva_asociaciones(self):
        parent = ServicioNivel1.objects.get(codigo="SE.12")
        parent.codigo = "N1.HUMANO"
        parent.save()
        import_catalog(ORIGINAL)
        self.assertEqual(ServicioNivel1.objects.count(), 12)
        self.assertEqual(ServicioNivel2.objects.get(codigo="SE.12.3").nivel1_id, parent.pk)

    def test_etiqueta_humana_preserva_mapeo_origen(self):
        kind = TipoServicio.objects.get(etiqueta="Demostration")
        kind.etiqueta = "Etiqueta humana"
        kind.save()
        execution = import_catalog(ORIGINAL).execution
        self.assertEqual(TipoServicio.objects.count(), 11)
        self.assertFalse(TipoServicio.objects.filter(etiqueta="Demostration").exists())
        origin = execution.registros.get(entidad="TIPO", valores_importados__etiqueta="Demostration")
        self.assertEqual(origin.valores_aplicados["etiqueta"], "Etiqueta humana")

    def test_texto_con_codigo_aparente_solo_se_almacena(self):
        payload = "__import__('os').system('orden-no-autorizada') <script>dato</script>"
        with changed_source(lambda book: setattr(book.active["I5"], "value", payload)) as file:
            with patch("os.system") as system, patch("subprocess.run") as process:
                import_catalog(file)
                system.assert_not_called()
                process.assert_not_called()
        self.assertEqual(ServicioNivel2.objects.get(codigo="SE.01.01").descripcion, payload)

    def test_error_futuro_no_elimina_importacion_valida_anterior(self):
        with changed_source(lambda book: setattr(book.active["K5"], "value", 101)) as file:
            with self.assertRaises(CatalogImportError):
                import_catalog(file)
        self.assertEqual(ServicioNivel1.objects.count(), 12)
        self.assertEqual(ServicioNivel2.objects.count(), 46)
        self.assertEqual(RegistroOrigen.objects.count(), 76)
        self.assertEqual(EjecucionImportacion.objects.filter(estado="COMPLETADA").count(), 1)
        self.assertEqual(EjecucionImportacion.objects.filter(estado="FALLIDA").count(), 1)


class ImportFailuresTests(TestCase):
    def test_comando_archivo_inexistente_es_error(self):
        with self.assertRaises(CommandError):
            command_report(ORIGINAL.parent / "archivo-no-existente-de-prueba.xlsx")
        self.assertEqual(EjecucionImportacion.objects.count(), 0)

    def test_error_estructura_persistido_sin_entidades(self):
        with changed_source(lambda book: setattr(book.active["A4"], "value", "INVALIDO")) as file:
            with self.assertRaises(CatalogImportError) as caught:
                import_catalog(file)
        execution = EjecucionImportacion.objects.get(pk=caught.exception.execution_id)
        self.assertEqual(execution.estado, "FALLIDA")
        self.assertEqual(ServicioNivel1.objects.count(), 0)
        self.assertEqual(ServicioNivel2.objects.count(), 0)
        self.assertTrue(execution.incidencias.filter(tipo="FALLO_FATAL").exists())

    def test_rollback_fallo_controlado_durante_persistencia(self):
        # Fallo deliberado SOLO de fixture para comprobar atomicidad, no evidencia
        # de un bug observado en desarrollo ni de una mejora de prompt.
        manual = ServicioNivel1.objects.create(codigo="MANUAL", nombre="Registro previo")

        def controlled_failure(execution, entry, *args):
            if entry.entity == "NIVEL2":
                raise RuntimeError("Fallo sintético deliberado de prueba")
            return write_origin(execution, entry, *args)

        with patch("imports.services.importer.write_origin", side_effect=controlled_failure):
            with self.assertRaises(CatalogImportError):
                import_catalog(ORIGINAL)
        self.assertEqual(list(ServicioNivel1.objects.values_list("pk", flat=True)), [manual.pk])
        self.assertEqual(ClaseServicio.objects.count(), 0)
        self.assertEqual(ServicioNivel2.objects.count(), 0)
        self.assertEqual(RegistroOrigen.objects.count(), 0)
        execution = EjecucionImportacion.objects.get()
        self.assertEqual(execution.estado, "FALLIDA")
        self.assertEqual(execution.creados, 0)
        self.assertEqual(execution.incidencias.count(), 1)

    def test_precision_no_se_redondea_silenciosamente(self):
        with changed_source(lambda book: setattr(book.active["K5"], "value", "0.0000001")) as file:
            with self.assertRaises(CatalogImportError):
                import_catalog(file)
        self.assertEqual(ServicioNivel2.objects.count(), 0)
        self.assertEqual(RegistroOrigen.objects.count(), 0)
        self.assertEqual(EjecucionImportacion.objects.get().estado, "FALLIDA")

    def test_colision_manual_sin_procedencia_se_conserva(self):
        parent = ServicioNivel1.objects.create(codigo="SE.01", nombre="Nombre manual")
        first = import_catalog(ORIGINAL).execution
        parent.refresh_from_db()
        self.assertEqual(parent.nombre, "Nombre manual")
        self.assertTrue(first.incidencias.filter(tipo="COLISION_SIN_PROCEDENCIA").exists())
        import_catalog(ORIGINAL)
        parent.refresh_from_db()
        self.assertEqual(parent.nombre, "Nombre manual")

    def test_no_reactiva_catalogo_manual_inactivo(self):
        classification = ClaseServicio.objects.create(etiqueta="A DEMANDA", estado=False)
        with self.assertRaises(CatalogImportError):
            import_catalog(ORIGINAL)
        classification.refresh_from_db()
        self.assertFalse(classification.estado)
        self.assertEqual(ClaseServicio.objects.count(), 1)
        self.assertEqual(ServicioNivel2.objects.count(), 0)
