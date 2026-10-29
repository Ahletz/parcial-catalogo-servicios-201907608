"""Datos demo Service Desk idempotentes, creados por los servicios de aplicación.

Cada escenario se identifica por un título «[DEMO] …»; si ya existe se omite.
Los tickets recorren los flujos reales (sin escribir estados a mano), así que la
demo también ejercita guardas, permisos y bitácora. Requiere import_catalog y
seed_demo previos; usa CI generados si existen.
"""

import json
import os
from datetime import timedelta

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import Usuario
from catalog.models import ServicioNivel2
from cmdb.models import CI
from config.domain import domain_transaction
from organization.models import Puesto
from processes.catalogo import Afectacion, NivelSoporte, Proceso, SubtipoRequisicion, TipoTicket
from service_desk import servicios as sd
from service_desk.models import (
    ArticuloConocimiento, AsignacionRolSD, ColaServiceDesk, MembresiaCola, RolServiceDesk,
    Ticket,
)

USUARIOS = (
    ("solicitante.demo", "Solicitante demo", (RolServiceDesk.SOLICITANTE,)),
    ("agente.demo", "Agente demo", (RolServiceDesk.AGENTE,)),
    ("agente2.demo", "Agente nivel 2 demo", ()),
    ("aprobador.demo", "Aprobador demo", (RolServiceDesk.APROBADOR, RolServiceDesk.SOLICITANTE)),
)
H = timedelta(hours=1)
COLAS = (
    ("NS-N2", "Nuevos servicios", Proceso.NUEVOS_SERVICIOS, NivelSoporte.SOPORTE_TECNICO, 8, 240),
    ("CAM-N3", "Cambios", Proceso.CAMBIOS, NivelSoporte.INGENIEROS, 8, 120),
    ("INC-N1", "Incidentes mesa de ayuda", Proceso.INCIDENTES, NivelSoporte.HELP_DESK, 1, 8),
    ("INC-N2", "Incidentes soporte técnico", Proceso.INCIDENTES, NivelSoporte.SOPORTE_TECNICO,
     2, 24),
    ("EVT-N1", "Eventos de monitoreo", Proceso.EVENTOS, NivelSoporte.HELP_DESK, 1, 4),
    ("PRO-N3", "Problemas", Proceso.PROBLEMAS, NivelSoporte.INGENIEROS, 24, 240),
    ("ACC-N1", "Accesos", Proceso.ACCESOS, NivelSoporte.HELP_DESK, 4, 24),
    ("ST-N1", "Servicios de tecnología", Proceso.SERVICIOS_TECNOLOGIA, NivelSoporte.HELP_DESK,
     4, 48),
)
ARTICULOS = (
    ("Restablecer contraseña de la cuenta local", "Cuentas",
     "Solicita el restablecimiento al administrador; nunca compartas tu contraseña.", True),
    ("Cómo registrar un incidente", "Service Desk",
     "Usa «Registrar ticket», tipo Incidente, indica el servicio y los CI afectados.", True),
    ("Solicitar acceso a un recurso", "Accesos",
     "Tipo Solicitud de acceso: beneficiario, recurso y permiso. Lo aprueba otra persona.", True),
    ("Diferencia entre incidente y requisición", "Service Desk",
     "Incidente: algo dejó de funcionar. Requisición: pides algo nuevo o un servicio existente.",
     True),
    ("Borrador: ventanas de mantenimiento", "Cambios", "Pendiente de revisión.", False),
)


class Command(BaseCommand):
    help = "Crea usuarios SD, ≥7 colas, FAQ y ≥35 tickets demo de los siete procesos."

    def handle(self, *args, **options):
        password = os.environ.get("DEMO_SD_PASSWORD")
        if not password or password == "CONFIGURAR_LOCALMENTE":
            raise CommandError("Configura DEMO_SD_PASSWORD antes de ejecutar seed_service_desk.")
        self.creados = {"usuarios": 0, "colas": 0, "membresias": 0, "articulos": 0,
                        "escenarios": 0, "escenarios_existentes": 0}
        try:
            with domain_transaction():
                self.preparar(password)
                self.escenarios()
        except ValidationError as error:
            raise CommandError("Demo inválida: " + "; ".join(error.messages)) from error
        demo = Ticket.objects.filter(titulo__startswith="[DEMO]")
        resultado = {
            **self.creados, "tickets_demo": demo.count(),
            "tickets_total": Ticket.objects.count(), "colas": ColaServiceDesk.objects.count(),
            "por_proceso": {p: demo.filter(proceso=p).count() for p in Proceso.values},
            "estados_distintos": demo.values("estado").distinct().count(),
        }
        self.stdout.write(json.dumps(resultado, ensure_ascii=False, sort_keys=True))

    # ------------------------------------------------------------------ base
    def preparar(self, password):
        puesto = Puesto.objects.filter(codigo="DEMO", seccion__codigo="DEMO").first()
        self.admin = Usuario.objects.filter(rol=Usuario.Rol.ADMINISTRADOR, is_active=True).order_by(
            "pk").first()
        self.consulta = Usuario.objects.filter(identificador="consulta.demo").first()
        if puesto is None or self.admin is None or self.consulta is None:
            raise CommandError("Ejecuta import_catalog y seed_demo antes de seed_service_desk.")
        self.seccion = puesto.seccion
        self.u = {}
        for identificador, nombre, roles in USUARIOS:
            user = Usuario.objects.filter(identificador=identificador).first()
            if user is None:
                candidato = Usuario(identificador=identificador, nombre=nombre,
                                    rol=Usuario.Rol.OPERATIVO, puesto=puesto)
                validate_password(password, candidato)
                user = Usuario.objects.create_user(identificador, nombre, puesto, password,
                                                   rol=Usuario.Rol.OPERATIVO)
                self.creados["usuarios"] += 1
            elif user.rol != Usuario.Rol.OPERATIVO or not user.is_active:
                raise CommandError(f"La cuenta {identificador} existe con otro rol o inactiva.")
            for rol in roles:
                if not AsignacionRolSD.objects.filter(usuario=user, rol=rol).exists():
                    AsignacionRolSD(usuario=user, rol=rol).save()
            self.u[identificador.split(".")[0]] = user
        self.colas = {}
        for codigo, nombre, proceso, nivel, atencion, resolucion in COLAS:
            cola = ColaServiceDesk.objects.filter(codigo=codigo).first()
            if cola is None:
                cola = ColaServiceDesk(
                    codigo=codigo, nombre=nombre, proceso=proceso, nivel_soporte=nivel,
                    descripcion=f"Cola demo de {nombre.lower()}",
                    objetivo_primera_atencion=atencion * H, objetivo_resolucion=resolucion * H,
                )
                cola.save()
                self.creados["colas"] += 1
            self.colas[codigo] = cola
        aprobables = {"NS-N2", "CAM-N3", "ACC-N1"}
        for codigo, cola in self.colas.items():
            if codigo != "INC-N2":
                self.membresia(cola, rol=RolServiceDesk.AGENTE, puede_atender=True,
                               puede_transferir=True)
            if codigo in aprobables:
                self.membresia(cola, rol=RolServiceDesk.APROBADOR, puede_aprobar=True)
        self.membresia(self.colas["INC-N2"], usuario=self.u["agente2"], puede_atender=True,
                       puede_transferir=True)
        self.membresia(self.colas["INC-N2"], rol=RolServiceDesk.AGENTE, puede_transferir=True)
        # Demostración: CONSULTA con membresía de atención sigue siendo solo lectura.
        self.membresia(self.colas["INC-N1"], usuario=self.consulta, puede_atender=True)
        for titulo, categoria, contenido, publicado in ARTICULOS:
            if not ArticuloConocimiento.objects.filter(titulo=titulo).exists():
                ArticuloConocimiento(titulo=titulo, categoria=categoria, contenido=contenido,
                                     publicado=publicado).save()
                self.creados["articulos"] += 1
        self.servicios = list(ServicioNivel2.objects.filter(activo=True).order_by("codigo")[:12])
        self.cis = list(CI.objects.filter(estado=True, clasificacion__es_dispositivo=True)
                        .order_by("codigo")[:12])

    def membresia(self, cola, usuario=None, rol="", **banderas):
        filtro = {"usuario": usuario} if usuario else {"rol": rol}
        if not MembresiaCola.objects.filter(cola=cola, **filtro).exists():
            MembresiaCola(cola=cola, usuario=usuario, rol=rol, **banderas).save()
            self.creados["membresias"] += 1

    # ----------------------------------------------------------- utilidades
    def crear(self, titulo, tipo, cola, n, subtipo="", detalle=None, con_ci=False,
              prioridad=3, actor=None):
        actor = actor or self.u["solicitante"]
        cis = [self.cis[n % len(self.cis)]] if con_ci and self.cis else []
        return sd.crear_ticket(
            actor, tipo=tipo, subtipo=subtipo, servicio=self.servicios[n % len(self.servicios)],
            cola=self.colas[cola], titulo=f"[DEMO] {titulo}", descripcion=f"Ticket demo: {titulo}.",
            prioridad=prioridad, impacto="MEDIO", urgencia="MEDIO", canal="PORTAL", cis=cis,
            motivo_sin_ci="" if cis else "Solicitud sin CI identificable en la demo.",
            detalle=detalle,
        )

    def paso(self, ticket, accion, actor=None, motivo="", **datos):
        return sd.ejecutar_accion(actor or self.u["agente"], ticket.pk, accion, motivo, datos)

    def tomar(self, ticket, actor=None):
        return sd.tomar_ticket(actor or self.u["agente"], ticket.pk)

    def escenario(self, clave, funcion):
        if Ticket.objects.filter(titulo__startswith=f"[DEMO] {clave}").exists():
            self.creados["escenarios_existentes"] += 1
            return
        funcion(clave)
        self.creados["escenarios"] += 1

    # ------------------------------------------------------------ procesos
    def escenarios(self):
        for n in range(1, 6):
            self.escenario(f"NS-{n}", lambda c, n=n: self.nuevo_servicio(c, n))
            self.escenario(f"CAM-{n}", lambda c, n=n: self.cambio(c, n))
            self.escenario(f"EVT-{n}", lambda c, n=n: self.evento(c, n))
            self.escenario(f"ACC-{n}", lambda c, n=n: self.acceso(c, n))
            self.escenario(f"ST-{n}", lambda c, n=n: self.servicio_tecnologia(c, n))
        for n, categoria in enumerate(("I0", "I1", "I2", "I3", "I4", "I5", "I6")):
            self.escenario(f"INC-{categoria}", lambda c, n=n, k=categoria: self.incidente(c, n, k))
        for n in range(1, 6):
            self.escenario(f"PRO-{n}", lambda c, n=n: self.problema(c, n))

    def nuevo_servicio(self, clave, n):
        t = self.crear(f"{clave} nuevo servicio", TipoTicket.REQUISICION_SERVICIO, "NS-N2", n,
                       SubtipoRequisicion.NUEVO_SERVICIO,
                       {"necesidad": "Se requiere capacidad adicional del servicio."})
        if n == 1:
            return
        self.tomar(t)
        self.paso(t, "analizar")
        if n == 2:
            return
        self.paso(t, "enviar_aprobacion", viabilidad="Viable con recursos actuales.",
                  modo_resultado="VINCULAR", servicio_resultante=self.servicios[n].pk)
        if n == 3:
            return
        if n == 4:
            self.paso(t, "rechazar", self.u["aprobador"], "Duplica un servicio vigente.")
            self.paso(t, "cerrar", resolucion="Rechazado por duplicidad.")
            return
        self.paso(t, "aprobar", self.u["aprobador"])
        self.paso(t, "implementar")
        self.paso(t, "cerrar", resolucion="Necesidad cubierta vinculando servicio existente.")

    def cambio(self, clave, n):
        t = self.crear(f"{clave} cambio", TipoTicket.SOLICITUD_CAMBIO, "CAM-N3", n, con_ci=True,
                       prioridad=2)
        if n == 1:
            return
        self.tomar(t)
        self.paso(t, "evaluar")
        self.paso(t, "enviar_aprobacion", impacto="ALTO", riesgo="MEDIO",
                  analisis_impacto="Afecta CI vinculados en ventana nocturna.",
                  plan_pruebas="Pruebas de humo y monitoreo 30 min.",
                  plan_reversion="Restaurar configuración previa respaldada.")
        if n == 2:
            return
        if n == 3:
            self.paso(t, "rechazar", self.u["aprobador"], "Riesgo no mitigado.")
            self.paso(t, "cerrar", resolucion="Rechazado; reformular.")
            return
        self.paso(t, "aprobar", self.u["aprobador"])
        self.paso(t, "planificar", fecha_planificada=timezone.now() + timedelta(days=2))
        if n == 4:
            return
        self.paso(t, "ejecutar")
        self.paso(t, "validar", resultado_validacion="Pruebas conformes.", exitoso=True)
        self.paso(t, "cerrar", resolucion="Cambio aplicado y validado.")

    def incidente(self, clave, n, categoria):
        afectaciones = {"I0": Afectacion.SIN_INTERRUPCION, "I6": Afectacion.SEGURIDAD}
        duraciones = {"I1": 2 * H, "I2": 6 * H, "I3": 30 * H, "I4": 240 * H, "I5": 960 * H}
        t = self.crear(f"{clave} incidente", TipoTicket.INCIDENTE, "INC-N1", n,
                       con_ci=n % 2 == 0, prioridad=1 if categoria == "I6" else 3)
        self.tomar(t)
        datos = {"afectacion": afectaciones.get(categoria, Afectacion.INTERRUPCION),
                 "categoria": categoria, "duracion_estimada": duraciones.get(categoria),
                 "redundancia": categoria == "I0"}
        if categoria == "I4":  # 10 días: hueco de la regla complementaria, sin sugerencia.
            datos["motivo_categoria"] = "Duración en el hueco 1 semana–1 mes; criterio del agente."
        self.paso(t, "clasificar", **datos)
        if categoria in {"I0", "I5"}:
            return
        self.paso(t, "diagnosticar")
        if categoria == "I3":
            sd.transferir_ticket(self.u["agente"], t.pk, self.colas["INC-N2"],
                                 "Requiere soporte técnico de nivel 2.", self.u["agente2"])
            return
        self.paso(t, "atender", diagnostico="Causa localizada en componente del servicio.")
        if categoria == "I4":
            self.paso(t, "escalar", motivo="Requiere proveedor externo.", nivel_escalamiento=4)
            return
        if categoria == "I6":
            sd.comentar(self.solicitante_de(t), t.pk, "¿Hay novedades del incidente?")
            sd.comentar(self.u["agente"], t.pk, "Revisando registros de acceso.", interno=True)
            sd.adjuntar(self.u["agente"], t.pk,
                        ContentFile(b"Registro sintetico de evidencia.\n", name="evidencia.txt"),
                        interno=True)
            return
        self.paso(t, "recuperar")
        self.paso(t, "resolver", solucion_aplicada="Reinicio controlado del componente.",
                  duracion_real=duraciones[categoria], resolucion="Servicio restablecido.")
        if categoria == "I2":
            sd.ejecutar_accion(self.solicitante_de(t), t.pk, "reabrir",
                               "El fallo volvió a presentarse.")
            return
        self.paso(t, "cerrar")

    def solicitante_de(self, ticket):
        return Usuario.objects.get(pk=ticket.solicitante_id)

    def evento(self, clave, n):
        categoria = {1: "E0", 2: "E1", 3: "E2", 4: "E3", 5: "E2"}[n]
        t, _ = sd.registrar_evento(
            self.u["agente"], clave_evento=f"DEMO-{clave}",
            servicio=self.servicios[n], cola=self.colas["EVT-N1"],
            titulo=f"[DEMO] {clave} evento {categoria}", descripcion="Alerta de monitoreo demo.",
            prioridad=2, impacto="MEDIO", urgencia="ALTO", canal="MONITOREO",
            cis=[self.cis[n]] if self.cis else [],
            motivo_sin_ci="" if self.cis else "Monitoreo sin CI registrado.",
            detalle={"fuente": "monitor-demo"},
        )
        if n == 5:
            return
        self.tomar(t)
        self.paso(t, "clasificar", categoria=categoria)
        if categoria == "E0":
            self.paso(t, "cerrar", resolucion="Evento programado registrado.")
            return
        self.paso(t, "evaluar", evaluacion="Evaluado por el operador.")
        if categoria == "E1":
            self.paso(t, "cerrar", resolucion="Sin respuesta operativa requerida.")
            return
        sd.vincular_incidente_evento(self.u["agente"], t.pk)
        sd.vincular_incidente_evento(self.u["agente"], t.pk)  # Reintento: no duplica.
        self.paso(t, "responder", respuesta="Incidente gestionado.")
        if categoria == "E2":
            self.paso(t, "cerrar", resolucion="Incidente derivado en curso.")

    def problema(self, clave, n):
        t = self.crear(f"{clave} problema", TipoTicket.PROBLEMA, "PRO-N3", n, actor=self.u["agente"])
        if n == 1:
            return
        incidente = Ticket.objects.get(titulo__startswith="[DEMO] INC-I1")
        sd.relacionar_tickets(self.u["agente"], incidente.pk, t.pk, "INCIDENTE_PROBLEMA",
                              "Incidentes recurrentes.")
        if n == 5:
            derivado = Ticket.objects.filter(eventos_origen__isnull=False).order_by("pk").first()
            if derivado:
                sd.relacionar_tickets(self.u["agente"], derivado.pk, t.pk, "INCIDENTE_PROBLEMA")
        self.tomar(t)
        self.paso(t, "investigar")
        if n == 2:
            return
        self.paso(t, "identificar_causa", causa_raiz="Fuga de memoria en el componente.")
        if n == 3:
            return
        self.paso(t, "registrar_error_conocido", workaround="Reinicio programado diario.")
        if n == 4:
            return
        cambio = Ticket.objects.get(titulo__startswith="[DEMO] CAM-5")
        sd.relacionar_tickets(self.u["agente"], t.pk, cambio.pk, "PROBLEMA_CAMBIO",
                              "Cambio correctivo.")
        self.paso(t, "planificar_solucion", solucion_definitiva="Actualizar componente.")
        self.paso(t, "resolver", resolucion="Corregido mediante el cambio vinculado.")
        self.paso(t, "cerrar")

    def acceso(self, clave, n):
        t = self.crear(f"{clave} acceso", TipoTicket.SOLICITUD_ACCESO, "ACC-N1", n, detalle={
            "beneficiario": self.u["solicitante"], "recurso": f"Carpeta compartida {n}",
            "permiso": "lectura", "accion": "PROVISION",
        })
        if n == 1:
            return
        self.tomar(t)
        self.paso(t, "enviar_aprobacion")
        if n == 2:
            return
        if n == 3:
            self.paso(t, "rechazar", self.u["aprobador"], "Sin justificación de negocio.")
            self.paso(t, "cerrar", resolucion="Acceso rechazado.")
            return
        self.paso(t, "aprobar", self.u["aprobador"])
        if n == 4:
            return
        self.paso(t, "provisionar", evidencia_ejecucion="Permiso otorgado en el directorio.")
        self.paso(t, "validar", resultado_validacion="Beneficiario confirma acceso.")
        self.paso(t, "cerrar", resolucion="Acceso provisto y validado.")

    def servicio_tecnologia(self, clave, n):
        t = self.crear(f"{clave} servicio existente", TipoTicket.REQUISICION_SERVICIO, "ST-N1", n,
                       SubtipoRequisicion.SERVICIO_EXISTENTE, con_ci=n == 1)
        if n == 1:
            return
        self.tomar(t)
        self.paso(t, "validar", resultado_validacion="Solicitud dentro del catálogo.")
        if n == 2:
            return
        self.paso(t, "asignar")
        self.paso(t, "iniciar_cumplimiento")
        if n == 3:
            return
        self.paso(t, "cumplir", detalle_cumplimiento="Configuración entregada.",
                  resolucion="Servicio cumplido.")
        if n == 4:
            return
        sd.ejecutar_accion(self.u["solicitante"], t.pk, "confirmar")
        self.paso(t, "cerrar")
