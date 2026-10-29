"""Genera un conjunto sintético reproducible de dispositivos CMDB.

Idempotente por código: la misma semilla produce los mismos códigos y una
segunda ejecución no crea ni modifica registros existentes (conserva cambios
humanos). Todos los registros pasan por save()/full_clean del dominio.
Clases bajo Hardware/Software son del conjunto sintético (D57), no de la fuente.
"""

import json
import random
from collections import Counter

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Usuario
from catalog.models import ServicioNivel2
from config.domain import domain_transaction
from cmdb.models import CI, ClasificacionCI, RelacionCI, ServicioCI, TipoRelacionCI, UbicacionCI

ORIGEN_FUENTE = {"fuente": "CMDB.xlsx", "celdas": "C5:C6"}
ORIGEN_SINTETICO = {"fuente": "decision_proyecto_D57", "uso": "conjunto_sintetico"}

RAICES = (
    ("HW", "Hardware", True, ORIGEN_FUENTE),
    ("SW", "Software", False, ORIGEN_FUENTE),
)
# codigo, nombre, padre, prefijo, peso, esquema
CLASES = (
    ("HW-SRV", "Servidor", "HW", "SRV", 12, {
        "cpu_nucleos": {"tipo": "entero", "obligatorio": True},
        "memoria_gb": {"tipo": "entero", "obligatorio": True},
        "sistema_operativo": {"tipo": "texto", "obligatorio": True,
                              "opciones": ["Linux", "Windows Server"]},
        "direccion_ip": {"tipo": "ip"},
    }),
    ("HW-EST", "Estación de trabajo", "HW", "EST", 58, {
        "cpu_nucleos": {"tipo": "entero", "obligatorio": True},
        "memoria_gb": {"tipo": "entero", "obligatorio": True},
        "sistema_operativo": {"tipo": "texto", "obligatorio": True,
                              "opciones": ["Linux", "Windows", "macOS"]},
        "direccion_ip": {"tipo": "ip"},
    }),
    ("HW-RED", "Equipo de red", "HW", "RED", 12, {
        "tipo_equipo": {"tipo": "texto", "obligatorio": True,
                        "opciones": ["switch", "router", "firewall", "access_point"]},
        "puertos": {"tipo": "entero", "obligatorio": True},
        "direccion_ip": {"tipo": "ip", "obligatorio": True},
    }),
    ("HW-ALM", "Almacenamiento", "HW", "ALM", 6, {
        "capacidad_tb": {"tipo": "numero", "obligatorio": True},
        "raid": {"tipo": "texto", "opciones": ["RAID1", "RAID5", "RAID6", "RAID10"]},
    }),
    ("HW-IMP", "Impresora", "HW", "IMP", 12, {
        "tecnologia": {"tipo": "texto", "obligatorio": True, "opciones": ["laser", "inyeccion"]},
        "en_red": {"tipo": "booleano", "obligatorio": True},
        "direccion_ip": {"tipo": "ip"},
    }),
)
APLICACION = ("SW-APP", "Aplicación", "SW", "APP", 0, {
    "version": {"tipo": "texto", "obligatorio": True},
})
UBICACIONES = (
    ("UB-CPD", "Centro de procesamiento principal"), ("UB-ALT", "Sitio alterno"),
    ("UB-OF1", "Oficina central nivel 1"), ("UB-OF2", "Oficina central nivel 2"),
    ("UB-OF3", "Oficina central nivel 3"),
)
TIPOS = (
    ("DEPENDE_DE", "Depende de", True, False),
    ("ALOJADO_EN", "Alojado en", True, False),
    ("CONECTADO_A", "Conectado a", False, True),
)
APLICACIONES = 50


def ip(rng, prefijo):
    return f"10.{prefijo}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


def atributos(clase, rng):
    if clase == "HW-SRV":
        return {"cpu_nucleos": rng.choice([8, 16, 32, 64]),
                "memoria_gb": rng.choice([32, 64, 128, 256]),
                "sistema_operativo": rng.choice(["Linux", "Windows Server"]),
                "direccion_ip": ip(rng, 10)}
    if clase == "HW-EST":
        valores = {"cpu_nucleos": rng.choice([4, 8, 12]), "memoria_gb": rng.choice([8, 16, 32]),
                   "sistema_operativo": rng.choice(["Linux", "Windows", "macOS"])}
        if rng.random() < 0.6:  # IP opcional: no todas la tienen.
            valores["direccion_ip"] = ip(rng, 20)
        return valores
    if clase == "HW-RED":
        return {"tipo_equipo": rng.choice(["switch", "router", "firewall", "access_point"]),
                "puertos": rng.choice([8, 24, 48]), "direccion_ip": ip(rng, 1)}
    if clase == "HW-ALM":
        return {"capacidad_tb": rng.choice([10.0, 20.0, 50.0, 100.0]),
                "raid": rng.choice(["RAID1", "RAID5", "RAID6", "RAID10"])}
    valores = {"tecnologia": rng.choice(["laser", "inyeccion"]), "en_red": rng.random() < 0.7}
    if valores["en_red"]:
        valores["direccion_ip"] = ip(rng, 30)
    return valores


class Command(BaseCommand):
    help = "Genera ≥5,000 dispositivos CMDB sintéticos con semilla, relaciones y servicios."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=5000)
        parser.add_argument("--seed", type=int, default=2026)

    def handle(self, *args, count, seed, **options):
        if count < 1:
            raise CommandError("--count debe ser positivo.")
        responsables = list(Usuario.objects.filter(is_active=True).exclude(
            rol=Usuario.Rol.CONSULTA).order_by("pk"))
        servicios = list(ServicioNivel2.objects.filter(activo=True).order_by("codigo"))
        if not responsables:
            raise CommandError("No hay usuarios activos no CONSULTA; ejecuta seed_demo antes.")
        if not servicios:
            raise CommandError("No hay servicios activos; importa el catálogo antes.")
        try:
            with domain_transaction():
                resultado = self.generar(count, seed, responsables, servicios)
        except ValidationError as error:
            raise CommandError("Generación rechazada: " + "; ".join(error.messages)) from error
        self.stdout.write(json.dumps(resultado, ensure_ascii=False, sort_keys=True))

    def asegurar(self, model, codigo, **defaults):
        obj = model.objects.filter(codigo=codigo).first()
        if obj is None:
            obj = model(codigo=codigo, **defaults)
            obj.save()
        return obj

    def generar(self, count, seed, responsables, servicios):
        clases = {}
        for codigo, nombre, dispositivo, origen in RAICES:
            clases[codigo] = self.asegurar(ClasificacionCI, codigo, nombre=nombre,
                                           es_dispositivo=dispositivo, datos_origen=origen)
        for orden, (codigo, nombre, padre, _, _, esquema) in enumerate(CLASES + (APLICACION,)):
            clases[codigo] = self.asegurar(
                ClasificacionCI, codigo, nombre=nombre, padre=clases[padre], orden=orden,
                es_dispositivo=padre == "HW", esquema_atributos=esquema,
                datos_origen=ORIGEN_SINTETICO,
            )
            existente = clases[codigo]
            if (existente.esquema_atributos != esquema or existente.padre_id != clases[padre].pk
                    or existente.es_dispositivo != (padre == "HW")):
                # No se reutiliza en silencio una clase homónima ajena al generador.
                raise CommandError(
                    f"La clasificación {codigo} ya existe con otro padre/esquema/naturaleza; "
                    "revísala antes de generar."
                )
        ubicaciones = [self.asegurar(UbicacionCI, c, nombre=n, datos_origen=ORIGEN_SINTETICO)
                       for c, n in UBICACIONES]
        tipos = {c: self.asegurar(TipoRelacionCI, c, nombre=n, dirigida=d, permite_ciclos=p,
                                  datos_origen=ORIGEN_SINTETICO) for c, n, d, p in TIPOS}

        existentes = set(CI.objects.filter(codigo__startswith=f"CI-{seed}-")
                         .values_list("codigo", flat=True))
        creados = 0
        pesos = [c[4] for c in CLASES]
        for ordinal in range(1, count + 1):
            codigo = f"CI-{seed}-{ordinal:05d}"
            if codigo in existentes:
                continue
            rng = random.Random(f"{seed}:{ordinal}")
            clase = rng.choices(CLASES, weights=pesos)[0]
            CI(
                codigo=codigo, nombre=f"{clase[3]}-{seed}-{ordinal:05d}",
                clasificacion=clases[clase[0]],
                ubicacion=ubicaciones[0 if clase[0] in {"HW-SRV", "HW-ALM", "HW-RED"}
                                      and rng.random() < 0.8 else rng.randrange(len(ubicaciones))],
                responsable=responsables[ordinal % len(responsables)],
                estado=rng.random() >= 0.02,
                descripcion=f"Dispositivo sintético {clase[1].lower()} #{ordinal}",
                atributos=atributos(clase[0], rng),
                datos_origen={**ORIGEN_SINTETICO, "seed": seed, "ordinal": ordinal},
            ).save()
            creados += 1

        apps_creadas = 0
        for indice in range(1, APLICACIONES + 1):
            codigo = f"APP-{seed}-{indice:03d}"
            if not CI.objects.filter(codigo=codigo).exists():
                CI(codigo=codigo, nombre=f"Aplicación sintética {indice:03d}",
                   clasificacion=clases["SW-APP"], ubicacion=ubicaciones[0],
                   responsable=responsables[indice % len(responsables)],
                   atributos={"version": f"{1 + indice % 4}.{indice % 10}"},
                   datos_origen={**ORIGEN_SINTETICO, "seed": seed, "aplicacion": indice}).save()
                apps_creadas += 1

        relaciones, vinculos = self.relacionar(seed, clases, tipos, servicios)
        conjunto = CI.objects.filter(codigo__startswith=f"CI-{seed}-")
        por_clase = Counter(conjunto.values_list("clasificacion__codigo", flat=True))
        por_nivel, por_raiz = Counter(), Counter()
        for clase in ClasificacionCI.objects.filter(codigo__in=por_clase):
            por_nivel[f"nivel_{clase.nivel}"] += por_clase[clase.codigo]
            por_raiz[clase.ruta_codigos()[0]] += por_clase[clase.codigo]
        return {
            "seed": seed, "solicitados": count, "creados": creados,
            "existentes_conservados": len(existentes),
            "total_conjunto": conjunto.count(),
            "dispositivos_conjunto": conjunto.filter(clasificacion__es_dispositivo=True).count(),
            "dispositivos_activos": conjunto.filter(estado=True).count(),
            "por_clasificacion": dict(sorted(por_clase.items())),
            "por_nivel": dict(sorted(por_nivel.items())),
            "por_categoria_raiz": dict(sorted(por_raiz.items())),
            "aplicaciones_software_creadas": apps_creadas,
            "relaciones_creadas": relaciones,
            "vinculos_servicio_creados": vinculos,
            "relaciones_total": RelacionCI.objects.count(),
            "vinculos_servicio_total": ServicioCI.objects.count(),
        }

    def relacionar(self, seed, clases, tipos, servicios):
        def activos(clase, limite):
            return list(CI.objects.filter(
                codigo__startswith=f"CI-{seed}-", clasificacion=clases[clase], estado=True
            ).order_by("codigo")[:limite])

        servidores, red = activos("HW-SRV", 300), activos("HW-RED", 60)
        almacen = activos("HW-ALM", 40)
        apps = list(CI.objects.filter(codigo__startswith=f"APP-{seed}-").order_by("codigo"))
        if not (servidores and red and almacen):
            return 0, 0
        pares = []
        for i, app in enumerate(apps):
            pares.append(("ALOJADO_EN", app, servidores[i % len(servidores)]))
        for i, servidor in enumerate(servidores):
            pares.append(("DEPENDE_DE", servidor, red[i % len(red)]))
            if i % 3 == 0:
                pares.append(("DEPENDE_DE", servidor, almacen[i % len(almacen)]))
        for i in range(len(red)):  # Anillo: ciclo permitido en un tipo no dirigido.
            a, b = red[i], red[(i + 1) % len(red)]
            if a.pk != b.pk:
                pares.append(("CONECTADO_A", *sorted((a, b), key=lambda ci: ci.pk)))
        existentes = set(RelacionCI.objects.values_list("tipo__codigo", "origen_id", "destino_id"))
        creadas = 0
        for tipo, origen, destino in pares:
            if (tipo, origen.pk, destino.pk) in existentes:
                continue
            RelacionCI(tipo=tipos[tipo], origen=origen, destino=destino).save()
            existentes.add((tipo, origen.pk, destino.pk))
            creadas += 1
        vinculos = 0
        actuales = set(ServicioCI.objects.values_list("ci_id", "servicio_id"))
        for i, app in enumerate(apps):
            servicio = servicios[i % len(servicios)]
            for ci in (app, servidores[i % len(servidores)]):
                if (ci.pk, servicio.pk) not in actuales:
                    ServicioCI(ci=ci, servicio=servicio).save()
                    actuales.add((ci.pk, servicio.pk))
                    vinculos += 1
        return creadas, vinculos
