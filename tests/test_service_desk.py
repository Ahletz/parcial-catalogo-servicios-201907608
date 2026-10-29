"""Escenarios SD-P01–SD-P17 (T §11). SD-P18 es operativo: scripts/verify-persistence.sh.

Los números SD-Pxx no equivalen a PP2-Pxx (D32). Datos exclusivamente sintéticos.
"""

import io
import threading
from datetime import timedelta
from unittest import mock

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import Usuario
from catalog.models import ServicioNivel1, ServicioNivel2
from cmdb.grafos import impacto
from cmdb.models import CI, ClasificacionCI, RelacionCI, ServicioCI
from processes.catalogo import (
    Afectacion, CategoriaIncidente, SubtipoRequisicion, TipoTicket, sugerir_categoria_incidente,
)
from processes.models import Aprobacion, DetalleEvento
from service_desk import servicios as sd
from service_desk.grafos import cadena
from service_desk.indicadores import calcular
from service_desk.models import (
    AccionTicket, ArticuloConocimiento, ColaServiceDesk, Notificacion, ReclasificacionTicket,
    RelacionTicket, Ticket, TransferenciaTicket,
)
from service_desk.permisos import Capacidad, capacidades, puede_ver, puede_ver_internas
from .import_helpers import command_report
from .sd_helpers import SDFixtures, crear_sd_base
from .web_helpers import TEST_PASSWORD

H = timedelta(hours=1)


class ServiceDeskAcceptanceTests(SDFixtures, TestCase):
    def test_SD_P01_autenticacion_logout_inactivo_y_rechazo_sin_permiso(self):
        self.assertEqual(self.client.get("/service-desk/").status_code, 302)
        self.assertTrue(self.client.login(username="sol@sd.test", password=TEST_PASSWORD))
        self.assertEqual(self.client.get("/service-desk/").status_code, 200)
        # OPERATIVO no escribe en mantenimientos PP2.
        self.assertEqual(self.client.post("/datos/empresas/nuevo/", {"codigo": "X"}).status_code,
                         403)
        self.client.post("/logout/")
        self.assertEqual(self.client.get("/service-desk/tickets/").status_code, 302)
        self.client.force_login(self.consulta)
        self.assertEqual(self.client.get("/service-desk/tickets/nuevo/").status_code, 403)
        inactivo = Usuario.objects.create_user("inactivo@sd.test", "Inactivo", self.puesto,
                                               TEST_PASSWORD, rol=Usuario.Rol.OPERATIVO,
                                               is_active=False)
        self.assertFalse(self.client.login(username=inactivo.identificador,
                                           password=TEST_PASSWORD))

    def test_SD_P03_generacion_cmdb_semilla_sin_duplicados(self):
        call_command("generate_cmdb", count=120, seed=77, stdout=io.StringIO())
        salida = io.StringIO()
        call_command("generate_cmdb", count=120, seed=77, stdout=salida)
        self.assertIn('"creados": 0', salida.getvalue())
        conjunto = CI.objects.filter(codigo__startswith="CI-77-")
        self.assertEqual(conjunto.count(), 120)
        self.assertEqual(conjunto.values("codigo").distinct().count(), 120)
        self.assertTrue(all(ci.clasificacion.es_dispositivo for ci in conjunto))
        sin_ip = conjunto.filter(clasificacion__codigo="HW-EST").exclude(
            atributos__has_key="direccion_ip")
        self.assertTrue(sin_ip.exists())  # IP opcional, no global.

    def test_SD_P03_generador_rechaza_clase_homonima_incompatible(self):
        hw = ClasificacionCI.objects.create(codigo="HW", nombre="Hardware", es_dispositivo=True)
        ClasificacionCI.objects.create(codigo="HW-SRV", nombre="Servidor", padre=hw,
                                       es_dispositivo=True)
        with self.assertRaises(CommandError):
            call_command("generate_cmdb", count=5, seed=78, stdout=io.StringIO())
        self.assertFalse(CI.objects.filter(codigo__startswith="CI-78-").exists())

    def test_SD_P04_jerarquia_cmdb_padre_inexistente_y_ciclos(self):
        self.assertEqual(self.srv.nivel, 2)
        self.assertEqual([n.codigo for n in self.srv.ruta()], ["FX-HW", "FX-SRV"])
        with self.assertRaises(ValidationError):
            ClasificacionCI(codigo="X", nombre="X", padre_id=999999).save()
        self.hw.padre = self.srv
        with self.assertRaises(ValidationError):
            self.hw.save()  # Ciclo HW → HW-SRV → HW.
        RelacionCI.objects.create(tipo=self.depende, origen=self.ci, destino=self.ci2)
        with self.assertRaises(ValidationError):
            RelacionCI(tipo=self.depende, origen=self.ci2, destino=self.ci).save()
        with self.assertRaises(ValidationError):
            RelacionCI(tipo=self.alojado, origen=self.ci2, destino=self.ci).save()  # Mezcla tipos.
        a, b = sorted((self.ci, self.app), key=lambda c: c.pk)
        RelacionCI.objects.create(tipo=self.conectado, origen=a, destino=b)
        self.assertEqual(RelacionCI.objects.count(), 2)

    def test_SD_P05_crear_ticket_valido_y_referencias_invalidas(self):
        ticket = self.crear(TipoTicket.INCIDENTE, "INC", cis=[self.ci])
        self.assertRegex(ticket.numero, r"^SD-\d{6}$")
        self.assertEqual(ticket.nivel1, self.n1)
        self.assertEqual(ticket.estado, "REGISTRADO")
        self.assertTrue(ticket.acciones.filter(accion="CREAR").exists())
        self.assertEqual(list(ticket.cis.all()), [self.ci])
        with self.assertRaises(ValidationError):
            self.crear(TipoTicket.INCIDENTE, "INC", servicio=self.desconocido)
        with self.assertRaises(ValidationError):
            self.crear(TipoTicket.INCIDENTE, "CAM")  # Cola de otro proceso.
        with self.assertRaises(ValidationError):
            self.crear(TipoTicket.INCIDENTE, "INC", motivo_sin_ci="")  # Sin CI ni motivo.
        with self.assertRaises(ValidationError):
            self.crear(TipoTicket.REQUISICION_SERVICIO, "ST")  # Falta subtipo.
        respuesta = self.client_post_ticket(cis="NO-EXISTE")
        self.assertContains(respuesta, "CI inexistentes")

    def client_post_ticket(self, **cambios):
        self.client.force_login(self.sol)
        datos = {"tipo": "INCIDENTE", "servicio": self.servicio.pk, "cola": self.cola["INC"].pk,
                 "titulo": "Por HTTP", "descripcion": "x", "prioridad": 3, "impacto": "MEDIO",
                 "urgencia": "MEDIO", "canal": "PORTAL", "motivo_sin_ci": "Sin CI"}
        datos.update(cambios)
        return self.client.post("/service-desk/tickets/nuevo/", datos, follow=True)

    def test_SD_P06_colas_por_rol_y_usuario_acceso_permitido_y_denegado(self):
        ticket = self.incidente()
        self.assertIn(Capacidad.ATENDER, capacidades(self.ag, self.cola["INC"]))  # Por rol.
        self.assertIn(Capacidad.ATENDER, capacidades(self.ag2, self.cola["INC2"]))  # Por usuario.
        self.assertEqual(capacidades(self.ag2, self.cola["INC"]), frozenset())
        # CONSULTA con membresía de atender/transferir/aprobar: solo consultar.
        self.assertEqual(capacidades(self.consulta, self.cola["INC"]), {Capacidad.CONSULTAR})
        self.assertTrue(puede_ver(self.consulta, ticket))
        self.assertFalse(puede_ver_internas(self.consulta, ticket))
        for operacion in (lambda: sd.comentar(self.consulta, ticket.pk, "x"),
                          lambda: sd.liberar_ticket(self.consulta, ticket.pk, "x"),
                          lambda: self.paso(ticket, "clasificar", self.consulta)):
            with self.assertRaises(PermissionDenied):
                operacion()
        otro = self.crear(TipoTicket.INCIDENTE, "INC", actor=self.otro_sol)
        self.assertFalse(puede_ver(self.sol, otro))
        self.client.force_login(self.sol)
        self.assertEqual(self.client.get(f"/service-desk/tickets/{otro.numero}/").status_code, 403)
        self.assertEqual(self.client.get(f"/service-desk/tickets/{ticket.numero}/").status_code,
                         200)
        sd.comentar(self.ag, ticket.pk, "Nota reservada", interno=True)
        respuesta = self.client.get(f"/service-desk/tickets/{ticket.numero}/")
        self.assertNotContains(respuesta, "Nota reservada")
        self.client.force_login(self.consulta)
        self.client.post(f"/service-desk/tickets/{ticket.numero}/", {"operacion": "tomar"})
        self.assertEqual(Ticket.objects.get(pk=ticket.pk).responsable, self.ag)
        with self.assertRaises(ValidationError):  # CONSULTA nunca es responsable.
            sd.asignar_ticket(self.ag, ticket.pk, self.consulta, "x")

    def test_SD_P08_transferencia_historial_destino_y_adjuntos(self):
        ticket = self.incidente()
        with self.assertRaises(ValidationError):
            sd.transferir_ticket(self.ag, ticket.pk, self.cola["CAM"], "otro proceso")
        with self.assertRaises(ValidationError):
            sd.transferir_ticket(self.ag, ticket.pk, self.cola["INC2"], "  ")
        with self.assertRaises(PermissionDenied):
            sd.transferir_ticket(self.ag2, ticket.pk, self.cola["INC2"], "sin capacidad")
        sd.transferir_ticket(self.ag, ticket.pk, self.cola["INC2"], "Nivel 2", self.ag2)
        registro = TransferenciaTicket.objects.get(ticket=ticket)
        self.assertEqual((registro.cola_origen, registro.cola_destino), (self.cola["INC"],
                                                                         self.cola["INC2"]))
        self.assertEqual((registro.responsable_anterior, registro.responsable_nuevo, registro.actor),
                         (self.ag, self.ag2, self.ag))
        self.assertTrue(ticket.acciones.filter(accion="TRANSFERIR", motivo="Nivel 2").exists())
        # Adjuntos: validación y descarga autorizada.
        ok = sd.adjuntar(self.sol, ticket.pk, ContentFile(b"evidencia\n", name="../x/a.txt"))
        self.assertEqual(ok.nombre_original, "a.txt")
        self.assertNotIn("..", ok.archivo.name)
        for archivo in (SimpleUploadedFile("a.exe", b"MZ"), SimpleUploadedFile(
                "a.pdf", b"no es pdf", content_type="application/pdf"),
                SimpleUploadedFile("a.png", b"\x89PNG\r\n\x1a\n", content_type="text/html")):
            with self.assertRaises(ValidationError):
                sd.adjuntar(self.sol, ticket.pk, archivo)
        interno = sd.adjuntar(self.ag2, ticket.pk, ContentFile(b"interno", name="i.txt"),
                              interno=True)
        url = f"/service-desk/adjuntos/{ok.identificador}/"
        self.assertEqual(self.client.get(url).status_code, 302)  # Sin sesión.
        self.client.force_login(self.sol)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["X-Content-Type-Options"], "nosniff")
        self.assertEqual(self.client.get(
            f"/service-desk/adjuntos/{interno.identificador}/").status_code, 403)
        self.client.force_login(self.otro_sol)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_SD_P09_siete_procesos_ruta_completa_y_transicion_invalida(self):
        sol, apr, ag = self.sol, self.apr, self.ag
        cerrados = []

        ns = self.crear(TipoTicket.REQUISICION_SERVICIO, "NS", subtipo=SubtipoRequisicion.NUEVO_SERVICIO,
                        detalle={"necesidad": "Servicio nuevo"})
        with self.assertRaises(ValidationError):
            sd.ejecutar_accion(ag, ns.pk, "cerrar")  # Fuera de orden.
        sd.tomar_ticket(ag, ns.pk)
        self.paso(ns, "analizar")
        with self.assertRaises(ValidationError):  # Duplicado del catálogo.
            self.paso(ns, "enviar_aprobacion", viabilidad="ok", modo_resultado="CREAR",
                      propuesta_codigo=self.servicio.codigo, propuesta_nombre="x",
                      propuesta_nivel1=self.n1.pk, propuesta_seccion=self.seccion.pk)
        self.paso(ns, "enviar_aprobacion", viabilidad="ok", modo_resultado="CREAR",
                  propuesta_codigo="WEB.1.99", propuesta_nombre="Servicio creado por SD",
                  propuesta_nivel1=self.n1.pk, propuesta_seccion=self.seccion.pk)
        self.paso(ns, "aprobar", apr)
        self.paso(ns, "implementar")
        self.paso(ns, "cerrar", resolucion="Implementado")
        self.assertTrue(ServicioNivel2.objects.filter(codigo="WEB.1.99", activo=True).exists())
        cerrados.append(ns)

        cam = self.crear(TipoTicket.SOLICITUD_CAMBIO, "CAM", cis=[self.ci])
        sd.tomar_ticket(ag, cam.pk)
        self.paso(cam, "evaluar")
        self.paso(cam, "enviar_aprobacion", impacto="ALTO", riesgo="BAJO", plan_pruebas="p",
                  plan_reversion="r")
        self.paso(cam, "aprobar", apr)
        self.paso(cam, "planificar", fecha_planificada=timezone.now())
        self.paso(cam, "ejecutar")
        self.paso(cam, "validar", resultado_validacion="ok", exitoso=True)
        self.paso(cam, "cerrar", resolucion="Aplicado")
        cerrados.append(cam)

        inc = self.incidente()
        self.paso(inc, "clasificar", afectacion=Afectacion.INTERRUPCION, categoria="I1",
                  duracion_estimada=2 * H)
        for accion, datos in (("diagnosticar", {}), ("atender", {"diagnostico": "d"}),
                              ("escalar", {"nivel_escalamiento": 2}), ("diagnosticar", {}),
                              ("atender", {}), ("recuperar", {}),
                              ("resolver", {"solucion_aplicada": "s", "resolucion": "r"})):
            self.paso(inc, accion, motivo="m", **datos)
        sd.ejecutar_accion(sol, inc.pk, "cerrar")
        cerrados.append(inc)

        evt, _ = sd.registrar_evento(ag, clave_evento="P09", **self.base_evento())
        sd.tomar_ticket(ag, evt.pk)
        self.paso(evt, "clasificar", categoria="E1")
        self.paso(evt, "evaluar", evaluacion="sin impacto")
        self.paso(evt, "cerrar")
        cerrados.append(evt)

        pro = self.crear(TipoTicket.PROBLEMA, "PRO", actor=ag)
        sd.relacionar_tickets(ag, inc.pk, pro.pk, "INCIDENTE_PROBLEMA")
        sd.tomar_ticket(ag, pro.pk)
        self.paso(pro, "investigar")
        self.paso(pro, "identificar_causa", causa_raiz="c")
        self.paso(pro, "registrar_error_conocido", workaround="w")
        self.paso(pro, "planificar_solucion", solucion_definitiva="s",
                  justificacion_sin_cambio="Configuración, no requiere cambio")
        self.paso(pro, "resolver", resolucion="r")
        self.paso(pro, "cerrar")
        cerrados.append(pro)

        acc = self.crear(TipoTicket.SOLICITUD_ACCESO, "ACC", detalle={
            "beneficiario": sol, "recurso": "R", "permiso": "lectura", "accion": "PROVISION"})
        sd.tomar_ticket(ag, acc.pk)
        self.paso(acc, "enviar_aprobacion")
        self.paso(acc, "aprobar", apr)
        with self.assertRaises(ValidationError):
            self.paso(acc, "revocar", evidencia_ejecucion="x")  # Acción no aprobada.
        self.paso(acc, "provisionar", evidencia_ejecucion="hecho")
        self.paso(acc, "validar", resultado_validacion="ok")
        self.paso(acc, "cerrar", resolucion="ok")
        cerrados.append(acc)

        st = self.crear(TipoTicket.REQUISICION_SERVICIO, "ST",
                        subtipo=SubtipoRequisicion.SERVICIO_EXISTENTE)
        sd.tomar_ticket(ag, st.pk)
        self.paso(st, "validar", resultado_validacion="ok")
        self.paso(st, "asignar")
        self.paso(st, "iniciar_cumplimiento")
        self.paso(st, "cumplir", detalle_cumplimiento="d", resolucion="r")
        with self.assertRaises(PermissionDenied):
            self.paso(st, "confirmar")  # Solo el solicitante confirma.
        sd.ejecutar_accion(sol, st.pk, "confirmar")
        self.paso(st, "cerrar")
        cerrados.append(st)

        for ticket in cerrados:
            ticket.refresh_from_db()
            self.assertEqual(ticket.estado, "CERRADO", ticket.proceso)
            self.assertIsNotNone(ticket.fecha_cierre)
        self.assertEqual(len({t.proceso for t in cerrados}), 7)
        with self.assertRaises(ValidationError):
            self.paso(st, "validar")  # Ticket cerrado.

    def base_evento(self, **extra):
        datos = dict(servicio=self.servicio, cola=self.cola["EVT"], titulo="Evento",
                     descripcion="alerta", prioridad=2, impacto="MEDIO", urgencia="ALTO",
                     canal="MONITOREO", cis=[self.ci], motivo_sin_ci="")
        datos.update(extra)
        return datos

    def test_SD_P10_cambio_sin_aprobacion_y_autoaprobacion_rechazados(self):
        cam = self.crear(TipoTicket.SOLICITUD_CAMBIO, "CAM", cis=[self.ci])
        sd.tomar_ticket(self.ag, cam.pk)
        self.paso(cam, "evaluar")
        with self.assertRaises(ValidationError):
            self.paso(cam, "ejecutar")
        self.paso(cam, "enviar_aprobacion", impacto="ALTO", riesgo="ALTO", plan_pruebas="p",
                  plan_reversion="r")
        with self.assertRaises(PermissionDenied):
            self.paso(cam, "aprobar")  # Agente sin capacidad aprobar.
        self.paso(cam, "aprobar", self.apr)
        self.paso(cam, "planificar", fecha_planificada=timezone.now())
        sd.actualizar_detalle(self.ag, cam.pk, {"plan_reversion": "otro plan"})
        with self.assertRaises(ValidationError):
            self.paso(cam, "ejecutar")  # Contenido distinto del aprobado.
        cam.refresh_from_db()
        self.assertEqual(cam.estado, "PLANIFICADO")
        # Defensa del modelo: sin aprobación en el ciclo vigente, ni un save directo ejecuta.
        cam.estado = "EJECUCION"
        sin_ciclo = lambda ticket: timezone.now() + timedelta(days=1)  # noqa: E731
        with mock.patch.object(Ticket, "inicio_ciclo_proceso", sin_ciclo):
            with self.assertRaises(ValidationError):
                cam.save()
        # Accesos: el solicitante (con rol aprobador) no puede autoaprobarse.
        acc = self.crear(TipoTicket.SOLICITUD_ACCESO, "ACC", actor=self.apr, detalle={
            "beneficiario": self.sol, "recurso": "R", "permiso": "p", "accion": "PROVISION"})
        sd.tomar_ticket(self.ag, acc.pk)
        self.paso(acc, "enviar_aprobacion")
        with self.assertRaises(ValidationError):
            self.paso(acc, "aprobar", self.apr)
        with self.assertRaises(ValidationError):
            Aprobacion(ticket=acc, aprobador=self.apr, decision="APROBADA", estado_origen="X",
                       huella="0" * 64).save()
        self.assertEqual(Ticket.objects.get(pk=acc.pk).estado, "PENDIENTE_APROBACION")

    def test_SD_P11_eventos_E0_E3_e_incidente_sin_duplicar(self):
        eventos = {}
        for categoria in ("E0", "E1", "E2", "E3"):
            evt, creado = sd.registrar_evento(self.ag, clave_evento=f"K-{categoria}",
                                              **self.base_evento())
            self.assertTrue(creado)
            sd.tomar_ticket(self.ag, evt.pk)
            self.paso(evt, "clasificar", categoria=categoria)
            eventos[categoria] = evt
        again, creado = sd.registrar_evento(self.ag, clave_evento="K-E0", **self.base_evento())
        self.assertEqual((again.pk, creado), (eventos["E0"].pk, False))
        with self.assertRaises(ValidationError):
            self.paso(eventos["E0"], "evaluar", evaluacion="x")
        self.paso(eventos["E0"], "cerrar")
        self.paso(eventos["E1"], "evaluar", evaluacion="x")
        with self.assertRaises(ValidationError):
            self.paso(eventos["E1"], "responder")
        with self.assertRaises(ValidationError):
            sd.vincular_incidente_evento(self.ag, eventos["E1"].pk)
        self.paso(eventos["E1"], "cerrar")
        for categoria in ("E2", "E3"):
            evt = eventos[categoria]
            self.paso(evt, "evaluar", evaluacion="impacto")
            with self.assertRaises(ValidationError):
                self.paso(evt, "responder")  # Sin incidente.
            incidente, creado = sd.vincular_incidente_evento(self.ag, evt.pk)
            repetido, creado2 = sd.vincular_incidente_evento(self.ag, evt.pk)
            self.assertEqual((incidente.pk, creado, creado2), (repetido.pk, True, False))
            self.assertEqual(incidente.proceso, "INCIDENTES")
            self.assertEqual(Notificacion.objects.filter(evento=evt).count(), 1)
            self.assertEqual(RelacionTicket.objects.filter(origen=evt).count(), 1)
            self.paso(evt, "responder", respuesta="ok")
            self.paso(evt, "cerrar")
        afectacion = DetalleEvento.objects.get(ticket=eventos["E3"]).incidente
        self.assertEqual(afectacion.definicion.detalle_de(afectacion).afectacion, "SEGURIDAD")
        self.assertEqual(Ticket.objects.filter(proceso="INCIDENTES").count(), 2)

    def test_SD_P12_categorias_I0_I6_y_regla_complementaria(self):
        casos = [
            (Afectacion.INTERRUPCION, 3 * H, "I1"),
            (Afectacion.INTERRUPCION, 3 * H + timedelta(seconds=1), "I2"),
            (Afectacion.DEGRADACION, 8 * H, "I2"), (Afectacion.INTERRUPCION, 48 * H, "I3"),
            (Afectacion.INTERRUPCION, timedelta(weeks=1), "I4"),
            (Afectacion.INTERRUPCION, timedelta(days=10), None),
            (Afectacion.INTERRUPCION, timedelta(days=30), "I5"),
            (Afectacion.INTERRUPCION, None, None), (Afectacion.SEGURIDAD, None, "I6"),
            (Afectacion.SIN_INTERRUPCION, None, "I0"),
        ]
        for afectacion, duracion, esperado in casos:
            self.assertEqual(sugerir_categoria_incidente(afectacion, duracion), esperado,
                             (afectacion, duracion))
        self.assertEqual(len(CategoriaIncidente.values), 7)
        for categoria, afectacion, duracion in (
            ("I0", Afectacion.SIN_INTERRUPCION, None), ("I1", "INTERRUPCION", 2 * H),
            ("I2", "DEGRADACION", 5 * H), ("I3", "INTERRUPCION", 30 * H),
            ("I4", "INTERRUPCION", 5 * 24 * H), ("I5", "INTERRUPCION", 40 * 24 * H),
            ("I6", "SEGURIDAD", None),
        ):
            inc = self.incidente()
            self.paso(inc, "clasificar", afectacion=afectacion, categoria=categoria,
                      duracion_estimada=duracion)
            self.assertEqual(inc.definicion.detalle_de(inc).categoria, categoria)
        inc = self.incidente()
        with self.assertRaises(ValidationError):  # Hueco sin sugerencia y sin motivo.
            self.paso(inc, "clasificar", afectacion="INTERRUPCION", categoria="I4",
                      duracion_estimada=timedelta(days=10))
        with self.assertRaises(ValidationError):
            self.paso(inc, "clasificar", afectacion="SIN_INTERRUPCION", categoria="I3",
                      motivo_categoria="no aplica")
        with self.assertRaises(ValidationError):
            self.paso(inc, "clasificar", afectacion="INTERRUPCION", categoria="I1",
                      duracion_estimada=-H)
        self.paso(inc, "clasificar", afectacion="INTERRUPCION", categoria="I4",
                  duracion_estimada=timedelta(days=10), motivo_categoria="Criterio del agente")

    def test_SD_P13_incidente_problema_cambio(self):
        evt, _ = sd.registrar_evento(self.ag, clave_evento="P13", **self.base_evento())
        sd.tomar_ticket(self.ag, evt.pk)
        self.paso(evt, "clasificar", categoria="E2")
        incidente, _ = sd.vincular_incidente_evento(self.ag, evt.pk)
        pro = self.crear(TipoTicket.PROBLEMA, "PRO", actor=self.ag)
        sd.tomar_ticket(self.ag, pro.pk)
        with self.assertRaises(ValidationError):
            self.paso(pro, "investigar")  # Sin incidentes.
        with self.assertRaises(ValidationError):
            sd.relacionar_tickets(self.ag, pro.pk, incidente.pk, "INCIDENTE_PROBLEMA")
        sd.relacionar_tickets(self.ag, incidente.pk, pro.pk, "INCIDENTE_PROBLEMA")
        self.paso(pro, "investigar")
        self.paso(pro, "identificar_causa", causa_raiz="c")
        with self.assertRaises(ValidationError):
            self.paso(pro, "planificar_solucion", solucion_definitiva="s")  # Sin cambio/justif.
        cam = self.crear(TipoTicket.SOLICITUD_CAMBIO, "CAM", actor=self.ag, cis=[self.ci])
        sd.relacionar_tickets(self.ag, pro.pk, cam.pk, "PROBLEMA_CAMBIO")
        self.paso(pro, "planificar_solucion", solucion_definitiva="s")
        grafo = cadena(self.admin, cam)
        self.assertEqual([t.proceso for t in grafo["nodos"]],
                         ["EVENTOS", "INCIDENTES", "PROBLEMAS", "CAMBIOS"])
        self.assertEqual(len(grafo["aristas"]), 3)
        self.client.force_login(self.ag)
        self.assertContains(self.client.get(f"/service-desk/tickets/{cam.numero}/grafo/"),
                            evt.numero)

    def test_SD_grafo_itsm_evento_incidente_problema_cambio(self):
        evt, _ = sd.registrar_evento(self.ag, clave_evento="GRAFO", **self.base_evento())
        sd.tomar_ticket(self.ag, evt.pk)
        self.paso(evt, "clasificar", categoria="E2")
        inc, _ = sd.vincular_incidente_evento(self.ag, evt.pk, cola_incidente=self.cola["INC"])
        pro = self.crear(TipoTicket.PROBLEMA, "PRO", actor=self.ag)
        sd.relacionar_tickets(self.ag, inc.pk, pro.pk, "INCIDENTE_PROBLEMA")
        cam = self.crear(TipoTicket.SOLICITUD_CAMBIO, "CAM", actor=self.ag, cis=[self.ci])
        sd.relacionar_tickets(self.ag, pro.pk, cam.pk, "PROBLEMA_CAMBIO")
        esperado = [evt.pk, inc.pk, pro.pk, cam.pk]
        aristas = [(evt.pk, inc.pk, "EVENTO_INCIDENTE"), (inc.pk, pro.pk, "INCIDENTE_PROBLEMA"),
                   (pro.pk, cam.pk, "PROBLEMA_CAMBIO")]
        for inicio in (evt, inc, pro, cam):  # La misma cadena desde cualquier punto.
            grafo = cadena(self.admin, inicio)
            self.assertEqual([t.pk for t in grafo["nodos"]], esperado)
            self.assertEqual(grafo["aristas"], aristas)
            self.assertEqual(grafo["ocultos"], 0)
        self.assertEqual([t.pk for t in cadena(self.admin, evt, profundidad=1)["nodos"]],
                         esperado[:2])
        self.assertEqual([t.pk for t in cadena(self.admin, evt, profundidad="abc")["nodos"]],
                         esperado)
        parcial = cadena(self.consulta, inc)  # CONSULTA solo ve la cola INC.
        self.assertEqual(([t.pk for t in parcial["nodos"]], parcial["ocultos"], parcial["aristas"]),
                         ([inc.pk], 3, []))

    def test_SD_reclasificacion_cambia_proceso_y_registra(self):
        inc = self.incidente()
        previo = Ticket.objects.get(pk=inc.pk)
        for actor, cola, motivo, error in (
                (self.ag, "PRO", "  ", ValidationError),       # Sin motivo.
                (self.ag, "CAM", "m", ValidationError),        # Cola de otro proceso.
                (self.consulta, "PRO", "m", PermissionDenied)):  # CONSULTA es solo lectura.
            with self.assertRaises(error):
                sd.reclasificar_ticket(actor, inc.pk, tipo=TipoTicket.PROBLEMA,
                                       cola_destino=self.cola[cola], motivo=motivo)
        self.assertFalse(ReclasificacionTicket.objects.filter(ticket=inc).exists())
        sd.reclasificar_ticket(self.ag, inc.pk, tipo=TipoTicket.PROBLEMA,
                               cola_destino=self.cola["PRO"], motivo="Causa recurrente")
        inc.refresh_from_db()
        self.assertEqual((inc.proceso, inc.tipo, inc.estado, inc.cola),
                         ("PROBLEMAS", TipoTicket.PROBLEMA, "REGISTRADO", self.cola["PRO"]))
        registro = ReclasificacionTicket.objects.get(ticket=inc)
        self.assertEqual(
            (registro.proceso_anterior, registro.proceso_nuevo, registro.tipo_anterior,
             registro.tipo_nuevo, registro.estado_anterior, registro.estado_nuevo),
            ("INCIDENTES", "PROBLEMAS", TipoTicket.INCIDENTE, TipoTicket.PROBLEMA,
             previo.estado, "REGISTRADO"))
        self.assertEqual(
            (registro.cola_anterior, registro.cola_nueva, registro.actor, registro.motivo),
            (self.cola["INC"], self.cola["PRO"], self.ag, "Causa recurrente"))
        self.assertIsNotNone(registro.created_at)
        bitacora = AccionTicket.objects.filter(ticket=inc, accion="RECLASIFICAR")
        self.assertEqual(
            {(a.campo, a.valor_anterior, a.valor_nuevo) for a in bitacora},
            {("proceso", "INCIDENTES", "PROBLEMAS"),
             ("tipo", TipoTicket.INCIDENTE, TipoTicket.PROBLEMA),
             ("estado", previo.estado, "REGISTRADO"),
             ("cola", self.cola["INC"].pk, self.cola["PRO"].pk)})
        self.assertEqual({(a.actor_id, a.motivo) for a in bitacora},
                         {(self.ag.pk, "Causa recurrente")})
        registro.motivo = "alterado"
        with self.assertRaises(ValidationError):
            registro.save()  # Registro inmutable.

    def test_SD_P14_ci_a_servicios_y_ciclos(self):
        otro = ServicioNivel2.objects.create(codigo="WEB.1.2", nombre="Otro", nivel1=self.n1,
                                             activo=True, seccion_responsable=self.seccion)
        RelacionCI.objects.create(tipo=self.alojado, origen=self.app, destino=self.ci)
        RelacionCI.objects.create(tipo=self.depende, origen=self.ci, destino=self.ci2)
        ServicioCI.objects.create(ci=self.app, servicio=self.servicio)
        ServicioCI.objects.create(ci=self.ci, servicio=otro)
        a, b = sorted((self.ci, self.ci2), key=lambda c: c.pk)
        RelacionCI.objects.create(tipo=self.conectado, origen=a, destino=b)  # Ciclo permitido.
        resultado = impacto(self.ci2, profundidad=5)
        self.assertEqual({c.codigo for c, _ in resultado["nodos"]}, {"CI-2", "CI-1", "APP-1"})
        self.assertEqual({s.codigo for s, _ in resultado["servicios"]}, {"WEB.1.1", "WEB.1.2"})
        self.assertEqual(len(impacto(self.ci2, profundidad=1)["nodos"]), 2)
        with self.assertRaises(ValidationError):
            RelacionCI(tipo=self.depende, origen=self.ci2, destino=self.app).save()
        self.client.force_login(self.consulta)
        self.assertContains(self.client.get("/cmdb/CI-2/grafo/?profundidad=5"), "WEB.1.2")
        self.assertEqual(self.client.get("/cmdb/CI-2/grafo/?profundidad=abc").status_code, 200)

    def test_SD_P15_cierre_sin_resolucion_reapertura_y_bitacora(self):
        inc = self.incidente()
        self.paso(inc, "clasificar", afectacion="INTERRUPCION", categoria="I1",
                  duracion_estimada=H)
        for accion in ("diagnosticar", "recuperar"):
            if accion == "recuperar":
                self.paso(inc, "atender", diagnostico="d")
            self.paso(inc, accion)
        with self.assertRaises(ValidationError):
            self.paso(inc, "resolver", solucion_aplicada="s")  # Sin resolución.
        self.paso(inc, "resolver", solucion_aplicada="s", resolucion="r")
        inc.refresh_from_db()
        self.assertIsNotNone(inc.fecha_resolucion)
        with self.assertRaises(ValidationError):
            sd.ejecutar_accion(self.sol, inc.pk, "reabrir")  # Sin motivo.
        sd.ejecutar_accion(self.sol, inc.pk, "reabrir", "Persiste")
        inc.refresh_from_db()
        self.assertEqual((inc.estado, inc.fecha_resolucion), ("ATENCION", None))
        acciones = AccionTicket.objects.filter(ticket=inc)
        self.assertTrue(acciones.filter(accion="REABRIR", motivo="Persiste",
                                        valor_anterior="RESUELTO").exists())
        accion = acciones.first()
        accion.motivo = "alterado"
        with self.assertRaises(ValidationError):
            accion.save()
        with self.assertRaises(ValidationError):
            acciones.delete()
        with self.assertRaises(ValidationError):
            acciones.update(motivo="x")
        ns = self.crear(TipoTicket.REQUISICION_SERVICIO, "NS",
                        subtipo=SubtipoRequisicion.NUEVO_SERVICIO, detalle={"necesidad": "n"})
        sd.tomar_ticket(self.ag, ns.pk)
        self.paso(ns, "analizar")
        self.paso(ns, "enviar_aprobacion", viabilidad="v", modo_resultado="VINCULAR",
                  servicio_resultante=self.servicio.pk)
        self.paso(ns, "rechazar", self.apr, "no")
        with self.assertRaises(ValidationError):
            self.paso(ns, "cerrar")  # Cierre sin resolución.
        # Reclasificación entre procesos con historia completa.
        inc2 = self.incidente()
        sd.reclasificar_ticket(self.ag, inc2.pk, tipo=TipoTicket.PROBLEMA,
                               cola_destino=self.cola["PRO"], motivo="Es recurrente")
        registro = ReclasificacionTicket.objects.get(ticket=inc2)
        self.assertEqual((registro.proceso_anterior, registro.proceso_nuevo, registro.estado_nuevo),
                         ("INCIDENTES", "PROBLEMAS", "REGISTRADO"))
        with self.assertRaises(ValidationError):
            sd.reclasificar_ticket(self.ag, inc2.pk, tipo=TipoTicket.PROBLEMA,
                                   cola_destino=self.cola["PRO"], motivo="x")

    def test_SD_P16_filtros_y_paginacion_cmdb_y_tickets(self):
        call_command("generate_cmdb", count=130, seed=16, stdout=io.StringIO())
        self.client.force_login(self.consulta)
        servidores = CI.objects.filter(codigo__startswith="CI-16-", clasificacion__codigo="HW-SRV")
        clase = ClasificacionCI.objects.get(codigo="HW-SRV")
        respuesta = self.client.get(f"/cmdb/?clasificacion={clase.pk}&estado=activo")
        self.assertEqual(respuesta.context["page"].paginator.count,
                         CI.objects.filter(clasificacion=clase, estado=True).count())
        hw = ClasificacionCI.objects.get(codigo="HW")
        pagina2 = self.client.get(f"/cmdb/?clasificacion={hw.pk}&page=2").context["page"]
        self.assertEqual((pagina2.number, len(pagina2.object_list)), (2, 50))
        self.assertEqual(self.client.get("/cmdb/?q=CI-16-0000").context["page"].paginator.count, 9)
        self.assertTrue(servidores.exists())
        responsable = CI.objects.filter(codigo__startswith="CI-16-").first().responsable
        self.assertGreater(self.client.get(
            f"/cmdb/?responsable={responsable.identificador}").context["page"].paginator.count, 0)
        app = CI.objects.get(codigo="APP-16-001")
        servicio = app.vinculos_servicio.first().servicio
        self.assertGreater(self.client.get(
            f"/cmdb/?servicio={servicio.codigo}").context["page"].paginator.count, 0)
        for prioridad in (1, 3):
            self.crear(TipoTicket.INCIDENTE, "INC", prioridad=prioridad)
        self.client.force_login(self.ag)
        lista = self.client.get("/service-desk/tickets/?proceso=INCIDENTES&prioridad=1")
        self.assertEqual(lista.context["page"].paginator.count, 1)
        orden = list(sd.tickets_en_cola(self.ag, self.cola["INC"]).values_list("prioridad",
                                                                              flat=True))
        self.assertEqual(orden, sorted(orden))

    def test_SD_P17_indicadores_con_datos_controlados(self):
        t0 = timezone.now().replace(microsecond=0) - timedelta(days=1)
        with mock.patch("django.utils.timezone.now", return_value=t0):
            atendido = self.crear(TipoTicket.REQUISICION_SERVICIO, "ST",
                                  subtipo=SubtipoRequisicion.SERVICIO_EXISTENTE)
            pendiente = self.crear(TipoTicket.REQUISICION_SERVICIO, "ST",
                                   subtipo=SubtipoRequisicion.SERVICIO_EXISTENTE)
            sd.tomar_ticket(self.ag, atendido.pk)
        with mock.patch("django.utils.timezone.now", return_value=t0 + timedelta(minutes=30)):
            self.paso(atendido, "validar", resultado_validacion="ok")
        with mock.patch("django.utils.timezone.now", return_value=t0 + timedelta(minutes=90)):
            self.paso(atendido, "asignar")
            self.paso(atendido, "iniciar_cumplimiento")
            self.paso(atendido, "cumplir", detalle_cumplimiento="d", resolucion="r")
        datos = calcular(Ticket.objects.filter(pk__in=[atendido.pk, pendiente.pk]),
                         corte=t0 + 3 * H)
        self.assertEqual(datos["total"], 2)
        self.assertEqual(datos["primera_atencion"], {"n": 1, "promedio_h": 0.5, "maximo_h": 0.5})
        self.assertEqual(datos["sin_primera_atencion"], 1)
        self.assertEqual(datos["resolucion"], {"n": 1, "promedio_h": 1.5, "maximo_h": 1.5})
        self.assertEqual(datos["antiguedad_abiertos"]["promedio_h"], 3.0)
        fila = datos["cumplimiento"]["ST"]
        self.assertEqual((fila["elegibles"], fila["cumplidos"], fila["porcentaje"],
                          fila["vencidos_abiertos"]), (1, 1, 100.0, 1))
        self.assertEqual((fila["atencion_elegibles"], fila["porcentaje_atencion"]), (1, 100.0))
        self.assertEqual(calcular(Ticket.objects.none())["resolucion"]["promedio_h"], None)
        self.client.force_login(self.ag)
        self.assertEqual(self.client.get("/service-desk/tablero/").status_code, 200)

    def test_SD_faq_publicados_y_busqueda(self):
        ArticuloConocimiento.objects.create(titulo="Clave", contenido="Restablecer", categoria="C",
                                            publicado=True)
        borrador = ArticuloConocimiento.objects.create(titulo="Borrador", contenido="x",
                                                       categoria="C")
        self.client.force_login(self.sol)
        self.assertContains(self.client.get("/service-desk/faq/?q=restablecer"), "Clave")
        self.assertNotContains(self.client.get("/service-desk/faq/"), "Borrador")
        self.assertEqual(self.client.get(f"/service-desk/faq/{borrador.pk}/").status_code, 403)

    def test_SD_administracion_solo_admin_y_renderiza(self):
        from django.urls import reverse

        from config.web import SD_ADMIN

        ArticuloConocimiento.objects.create(titulo="T", contenido="C", categoria="K")
        RelacionCI.objects.create(tipo=self.depende, origen=self.ci, destino=self.ci2)
        ServicioCI.objects.create(ci=self.ci, servicio=self.servicio)
        for slug, config in SD_ADMIN.items():
            instance = config.model.objects.first()
            rutas = [("entity-list", {}), ("entity-create", {}),
                     ("entity-edit", {"pk": instance.pk}),
                     ("entity-deactivate", {"pk": instance.pk})]
            for ruta, extra in rutas:
                url = reverse(ruta, kwargs={"entity": slug, **extra})
                with self.subTest(entity=slug, ruta=ruta):
                    self.client.logout()
                    self.assertEqual(self.client.get(url).status_code, 302)
                    self.client.force_login(self.admin)
                    self.assertEqual(self.client.get(url).status_code, 200)
                    if ruta != "entity-list":
                        self.client.force_login(self.ag)
                        self.assertEqual(self.client.post(url, {}).status_code, 403)
                        self.client.force_login(self.consulta)
                        self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertEqual(self.client.get("/service-desk/administracion/").status_code, 403)

    def test_SD_bajas_sin_huerfanos(self):
        inc = self.incidente()
        self.ag.is_active = False
        with self.assertRaises(ValidationError):
            self.ag.save()
        cola = ColaServiceDesk.objects.get(pk=self.cola["INC"].pk)
        cola.estado = False
        with self.assertRaises(ValidationError):
            cola.save()
        self.assertTrue(Ticket.objects.get(pk=inc.pk).abierto)


class ServiceDeskImportRegressionTests(TestCase):
    def test_SD_P02_catalogo_12_46_e_importacion_repetible(self):
        command_report()
        segundo = command_report()
        self.assertEqual((ServicioNivel1.objects.count(), ServicioNivel2.objects.count()), (12, 46))
        self.assertEqual((segundo["totales"]["creados"], segundo["totales"]["actualizados"]),
                         (0, 0))


class ServiceDeskConcurrencyTests(TransactionTestCase):
    def setUp(self):
        from organization.models import Area, Departamento, Empresa, Puesto, Seccion

        empresa = Empresa.objects.create(codigo="C", nombre="C")
        area = Area.objects.create(codigo="A", nombre="A", empresa=empresa)
        dep = Departamento.objects.create(codigo="D", nombre="D", area=area)
        self.seccion = Seccion.objects.create(codigo="S", nombre="S", departamento=dep)
        self.puesto = Puesto.objects.create(codigo="P", nombre="P", seccion=self.seccion)
        self.admin = Usuario.objects.create_user("adm@c.test", "A", self.puesto, TEST_PASSWORD,
                                                 rol=Usuario.Rol.ADMINISTRADOR)
        self.consulta = Usuario.objects.create_user("con@c.test", "C", self.puesto, TEST_PASSWORD)
        self.n1 = ServicioNivel1.objects.create(codigo="C.1", nombre="N1")
        self.servicio = ServicioNivel2.objects.create(codigo="C.1.1", nombre="N2", nivel1=self.n1,
                                                      activo=True, seccion_responsable=self.seccion)
        crear_sd_base(self)

    def test_SD_P07_dos_agentes_toman_el_mismo_ticket_solo_uno_gana(self):
        ticket = sd.crear_ticket(
            self.sol, tipo=TipoTicket.INCIDENTE, servicio=self.servicio, cola=self.cola["INC"],
            titulo="Concurrente", descripcion="x", prioridad=1, impacto="ALTO", urgencia="ALTO",
            canal="PORTAL", motivo_sin_ci="prueba")
        barrera, resultados = threading.Barrier(2), []

        def reclamar(agente):
            try:
                barrera.wait()
                sd.tomar_ticket(agente, ticket.pk)
                resultados.append(("gana", agente.pk))
            except sd.ConflictoAsignacion:
                resultados.append(("conflicto", agente.pk))
            finally:
                connection.close()

        hilos = [threading.Thread(target=reclamar, args=(a,)) for a in (self.ag, self.ag_b)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(30)
        self.assertEqual(sorted(r[0] for r in resultados), ["conflicto", "gana"])
        ganador = next(pk for estado, pk in resultados if estado == "gana")
        ticket.refresh_from_db()
        self.assertEqual(ticket.responsable_id, ganador)
        self.assertEqual(AccionTicket.objects.filter(ticket=ticket, accion="TOMAR").count(), 1)
