"""Fixtures sintéticas de Service Desk/CMDB para SD-P01–SD-P17."""

from datetime import timedelta

from accounts.models import Usuario
from cmdb.models import CI, ClasificacionCI, TipoRelacionCI, UbicacionCI
from processes.catalogo import Proceso, TipoTicket
from service_desk import servicios as sd
from service_desk.models import (
    AsignacionRolSD, ColaServiceDesk, MembresiaCola, RolServiceDesk,
)
from .web_helpers import TEST_PASSWORD, WebFixtures

COLAS = {
    "NS": Proceso.NUEVOS_SERVICIOS, "CAM": Proceso.CAMBIOS, "INC": Proceso.INCIDENTES,
    "INC2": Proceso.INCIDENTES, "EVT": Proceso.EVENTOS, "PRO": Proceso.PROBLEMAS,
    "ACC": Proceso.ACCESOS, "ST": Proceso.SERVICIOS_TECNOLOGIA,
}


def crear_sd_base(cls):
    """Usuarios OPERATIVO, roles, colas, membresías y una mini CMDB."""
    def operativo(identificador, *roles):
        user = Usuario.objects.create_user(identificador, identificador, cls.puesto, TEST_PASSWORD,
                                           rol=Usuario.Rol.OPERATIVO)
        for rol in roles:
            AsignacionRolSD.objects.create(usuario=user, rol=rol)
        return user

    cls.sol = operativo("sol@sd.test", RolServiceDesk.SOLICITANTE)
    cls.otro_sol = operativo("sol2@sd.test", RolServiceDesk.SOLICITANTE)
    cls.ag = operativo("ag@sd.test", RolServiceDesk.AGENTE)
    cls.ag_b = operativo("agb@sd.test", RolServiceDesk.AGENTE)
    cls.ag2 = operativo("ag2@sd.test")
    cls.apr = operativo("apr@sd.test", RolServiceDesk.APROBADOR, RolServiceDesk.SOLICITANTE)
    cls.cola = {}
    for codigo, proceso in COLAS.items():
        cls.cola[codigo] = ColaServiceDesk.objects.create(
            codigo=codigo, nombre=f"Cola {codigo}", proceso=proceso,
            objetivo_primera_atencion=timedelta(hours=1), objetivo_resolucion=timedelta(hours=2),
        )
        if codigo != "INC2":
            MembresiaCola.objects.create(cola=cls.cola[codigo], rol=RolServiceDesk.AGENTE,
                                         puede_atender=True, puede_transferir=True)
            MembresiaCola.objects.create(cola=cls.cola[codigo], rol=RolServiceDesk.APROBADOR,
                                         puede_aprobar=True)
    MembresiaCola.objects.create(cola=cls.cola["INC2"], usuario=cls.ag2, puede_atender=True)
    MembresiaCola.objects.create(cola=cls.cola["INC"], usuario=cls.consulta, puede_atender=True,
                                 puede_transferir=True, puede_aprobar=True)
    cls.hw = ClasificacionCI.objects.create(codigo="FX-HW", nombre="Hardware", es_dispositivo=True)
    cls.srv = ClasificacionCI.objects.create(codigo="FX-SRV", nombre="Servidor", padre=cls.hw,
                                             es_dispositivo=True)
    cls.sw = ClasificacionCI.objects.create(codigo="FX-SW", nombre="Software")
    cls.ubic = UbicacionCI.objects.create(codigo="UB", nombre="Centro de datos")
    cls.ci = CI.objects.create(codigo="CI-1", nombre="Servidor 1", clasificacion=cls.srv,
                               ubicacion=cls.ubic, responsable=cls.admin)
    cls.ci2 = CI.objects.create(codigo="CI-2", nombre="Servidor 2", clasificacion=cls.srv,
                                ubicacion=cls.ubic, responsable=cls.admin)
    cls.app = CI.objects.create(codigo="APP-1", nombre="Aplicación", clasificacion=cls.sw,
                                ubicacion=cls.ubic, responsable=cls.admin)
    cls.depende = TipoRelacionCI.objects.create(codigo="DEPENDE_DE", nombre="Depende de")
    cls.alojado = TipoRelacionCI.objects.create(codigo="ALOJADO_EN", nombre="Alojado en")
    cls.conectado = TipoRelacionCI.objects.create(codigo="CONECTADO_A", nombre="Conectado a",
                                                  dirigida=False, permite_ciclos=True)


class SDFixtures(WebFixtures):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        crear_sd_base(cls)

    def crear(self, tipo, cola, actor=None, subtipo="", detalle=None, cis=None, **extra):
        datos = dict(
            tipo=tipo, subtipo=subtipo, servicio=self.servicio, cola=self.cola[cola],
            titulo=f"Ticket {tipo}", descripcion="Descripción sintética", prioridad=3,
            impacto="MEDIO", urgencia="MEDIO", canal="PORTAL", cis=cis or [],
            motivo_sin_ci="" if cis else "Sin CI en la prueba", detalle=detalle,
        )
        datos.update(extra)
        return sd.crear_ticket(actor or self.sol, **datos)

    def paso(self, ticket, accion, actor=None, motivo="", **datos):
        return sd.ejecutar_accion(actor or self.ag, ticket.pk, accion, motivo, datos)

    def incidente(self, **extra):
        ticket = self.crear(TipoTicket.INCIDENTE, "INC", **extra)
        sd.tomar_ticket(self.ag, ticket.pk)
        return ticket
