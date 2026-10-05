"""Escenarios oficiales P06–P08, original real y PostgreSQL aislado."""

import json
from hashlib import sha256

from django.test import TestCase

from catalog.models import (
    ClaseServicio, CriticidadServicio, ServicioNivel1, ServicioNivel2, TipoServicio,
)
from imports.models import EjecucionImportacion, IncidenciaImportacion, RegistroOrigen
from imports.services.parser import ORIGINAL_SHA256

from .import_helpers import CLASSES, CRITICALITIES, ORIGINAL, TYPES, command_report


class OfficialImportAcceptanceTests(TestCase):
    def assert_original_state(self):
        self.assertEqual(ServicioNivel1.objects.count(), 12)
        self.assertEqual(ServicioNivel2.objects.count(), 46)
        for model, expected in (
            (ClaseServicio, CLASSES), (CriticidadServicio, CRITICALITIES), (TipoServicio, TYPES)
        ):
            self.assertEqual(set(model.objects.values_list("etiqueta", flat=True)), expected)
        self.assertEqual(ServicioNivel2.objects.filter(activo=True).count(), 42)
        self.assertEqual(ServicioNivel2.objects.filter(activo=False).count(), 1)
        self.assertEqual(ServicioNivel2.objects.filter(activo__isnull=True).count(), 3)
        self.assertEqual(sha256(ORIGINAL.read_bytes()).hexdigest(), ORIGINAL_SHA256)

    def test_P06_importar_original(self):
        report = command_report()
        self.assert_original_state()
        execution = EjecucionImportacion.objects.get(pk=report["ejecucion"])
        self.assertEqual(execution.estado, "COMPLETADA")
        self.assertEqual(execution.sha256, ORIGINAL_SHA256)
        self.assertEqual((execution.creados, execution.actualizados, execution.omitidos), (76, 0, 0))
        self.assertEqual((execution.filas_continuacion, execution.filas_sin_identidad), (49, 2))
        self.assertEqual(execution.registros.count(), 76)
        self.assertEqual(execution.incidencias.count(), 4)
        self.assertEqual(execution.observados, 4)
        self.assertEqual(execution.registros.filter(entidad="NIVEL1").count(), 12)
        self.assertEqual(execution.registros.filter(entidad="NIVEL2").count(), 46)
        print("P06 RESULTADO REAL:", json.dumps(report, ensure_ascii=False))

    def test_P07_repetir_importacion(self):
        first = command_report()
        before = list(ServicioNivel2.objects.order_by("pk").values())
        second = command_report()
        self.assert_original_state()
        self.assertEqual(list(ServicioNivel2.objects.order_by("pk").values()), before)
        self.assertEqual(second["totales"], {
            "creados": 0, "actualizados": 0, "omitidos": 76, "observados": 4,
        })
        self.assertNotEqual(first["ejecucion"], second["ejecucion"])
        self.assertEqual(EjecucionImportacion.objects.filter(estado="COMPLETADA").count(), 2)
        self.assertEqual(RegistroOrigen.objects.count(), 152)
        self.assertEqual(IncidenciaImportacion.objects.count(), 8)
        for entity, total in (("NIVEL1", 12), ("NIVEL2", 46), ("CLASE", 2), ("CRITICIDAD", 5), ("TIPO", 11)):
            self.assertEqual(second["detalle"][entity]["creados"], 0)
            self.assertEqual(second["detalle"][entity]["actualizados"], 0)
            self.assertEqual(second["detalle"][entity]["omitidos"], total)
        print("P07 PRIMERA REAL:", json.dumps(first, ensure_ascii=False))
        print("P07 SEGUNDA REAL:", json.dumps(second, ensure_ascii=False))

    def test_P08_se12_y_ausencias(self):
        report = command_report()
        parent = ServicioNivel1.objects.get(codigo="SE.12")
        self.assertEqual(ServicioNivel1.objects.filter(codigo="SE.12").count(), 1)
        self.assertEqual(parent.nombre, "Suministrar Analitica")
        origin = RegistroOrigen.objects.get(
            ejecucion_id=report["ejecucion"], servicio_n1=parent
        )
        self.assertEqual(origin.valores_originales["B99"]["valor"], "Suministrar Analitica")
        self.assertEqual(origin.valores_originales["B100"]["valor"], "Mantener Tableros de Control")
        self.assertTrue(IncidenciaImportacion.objects.filter(
            registro=origin, tipo="CONFLICTO_N1"
        ).exists())
        for code in ("SE.12.1", "SE.12.2", "SE.12.3"):
            service = ServicioNivel2.objects.get(codigo=code)
            self.assertEqual(service.codigo, code)
            self.assertEqual(service.nivel1_id, parent.pk)
            for field in (
                "activo", "clase_id", "criticidad_id", "tipo_id",
                "descripcion", "metrica", "minimo", "maximo",
            ):
                self.assertIsNone(getattr(service, field))
        service = ServicioNivel2.objects.get(codigo="SE.12.3")
        origin = RegistroOrigen.objects.get(
            ejecucion_id=report["ejecucion"], servicio_n2=service
        )
        self.assertIn("C101", origin.celdas)
        self.assertTrue(any(
            item["regla"] == "PREFIJO_EXACTO_Y_UNICO"
            for item in origin.transformaciones
        ))
        self.assertTrue(IncidenciaImportacion.objects.filter(
            registro=origin, tipo="INFERENCIA_N1"
        ).exists())
        self.assert_original_state()
        print("P08 RESULTADO REAL: canónico, ambos nombres, códigos, inferencia y NULL verificados.")
