from accounts.models import Usuario
from catalog.models import (
    ClaseServicio, CriticidadServicio, ServicioNivel1, ServicioNivel2, TipoServicio,
)
from organization.models import Area, Departamento, Empresa, Puesto, Seccion

# Datos públicos sintéticos; no son credenciales reales ni de evaluación.
TEST_PASSWORD = "Prueba-Sintetica-2026!"


class WebFixtures:
    @classmethod
    def setUpTestData(cls):
        cls.empresa = Empresa.objects.create(codigo="WEB", nombre="Empresa de prueba")
        cls.area = Area.objects.create(codigo="A", nombre="Área", empresa=cls.empresa)
        cls.departamento = Departamento.objects.create(codigo="D", nombre="Departamento", area=cls.area)
        cls.seccion = Seccion.objects.create(codigo="S", nombre="Sección", departamento=cls.departamento)
        cls.otra_seccion = Seccion.objects.create(codigo="OTRA", nombre="Otra sección", departamento=cls.departamento)
        cls.puesto = Puesto.objects.create(codigo="P", nombre="Puesto", seccion=cls.seccion)
        cls.otro_puesto = Puesto.objects.create(codigo="P", nombre="Otro puesto", seccion=cls.otra_seccion)
        cls.admin = Usuario.objects.create_user(
            "admin@web.test", "Administrador de prueba", cls.puesto, TEST_PASSWORD,
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        cls.consulta = Usuario.objects.create_user(
            "consulta@web.test", "Consulta de prueba", cls.puesto, TEST_PASSWORD,
        )
        cls.otro = Usuario.objects.create_user("otro@web.test", "Otra persona", cls.otro_puesto, TEST_PASSWORD)
        cls.n1 = ServicioNivel1.objects.create(codigo="WEB.1", nombre="Infraestructura")
        cls.otro_n1 = ServicioNivel1.objects.create(codigo="WEB.2", nombre="Comunicaciones")
        cls.clase = ClaseServicio.objects.create(etiqueta="A DEMANDA")
        cls.criticidad = CriticidadServicio.objects.create(etiqueta="Normal")
        cls.tipo = TipoServicio.objects.create(etiqueta="Demostration")
        cls.servicio = ServicioNivel2.objects.create(
            codigo="WEB.1.1", nombre="Análisis operativo", nivel1=cls.n1, activo=True,
            seccion_responsable=cls.seccion, clase=cls.clase,
            criticidad=cls.criticidad, tipo=cls.tipo, minimo=0, maximo=10,
        )
        cls.desconocido = ServicioNivel2.objects.create(
            codigo="WEB.2.1", nombre="Tablero externo", nivel1=cls.otro_n1, origen="IMPORTADO",
        )

    def service_data(self, **changes):
        data = {
            "codigo": "WEB.NUEVO", "nombre": "Nuevo servicio", "nivel1": self.n1.pk,
            "activo": "true", "clase": "", "criticidad": "", "tipo": "",
            "descripcion": "", "metrica": "", "minimo": "", "maximo": "",
            "seccion_responsable": self.seccion.pk, "usuario_responsable": "",
        }
        data.update(changes)
        return data
