# Evidencia de base/modelo — registro de trabajo

Fecha: 2026-10-04, America/Guatemala. Base: f5f39e3.
Este registro documenta comandos reales de esta fase; P01–P12 no se ejecutaron.
La ejecución final contra commit identificado se añadirá tras versionar código.

## Controles ejecutados durante el desarrollo

| Comando | Resultado real / código |
|---|---|
| python3 --version | 3.12.3 / 0; justifica contenedor Python 3.13. |
| docker version --format '{{.Server.Version}}' en sandbox | Acceso al socket denegado / 1; ejecución autorizada fuera de sandbox devuelve 28.3.3 / 0. |
| docker pull python:3.13-slim-bookworm | Imagen oficial descargada, digest fijado / 0. |
| docker pull postgres:17-bookworm | Imagen oficial descargada, digest fijado / 0. |
| Consulta urllib a PyPI público de seis paquetes | Versiones disponibles registradas en DECISIONES / 0. |
| docker compose -f compose.modelos.yaml build modelos (primero) | FALLÓ / 1: pip recibió + por línea RUN mal formada. |
| Mismo build tras corrección | PASÓ / 0: imagen construida. |
| docker run --rm catalogo-modelos-201907608-modelos python -m pip freeze | 13 paquetes; versiones transitivas fijadas / 0. |
| docker compose -f compose.modelos.yaml up -d db | Red interna/volumen/contenedor propios creados / 0. |
| docker compose -f compose.modelos.yaml run --rm modelos python manage.py check | Sin problemas, 0 silenciados / 0. |
| docker compose -f compose.modelos.yaml run --rm modelos python manage.py makemigrations organization accounts catalog imports | Cuatro 0001_initial generadas / 0. |
| docker compose -f compose.modelos.yaml run --rm modelos python manage.py migrate --noinput | Cuatro migraciones de aplicación y dependencias Django aplicadas / 0. |
| docker compose -f compose.modelos.yaml run --rm modelos python manage.py makemigrations --check --dry-run | No changes detected / 0. |
| docker run --rm catalogo-modelos-201907608-modelos python -m pip check | No broken requirements found / 0. |
| docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests --keepdb --verbosity 2 (primero) | FALLÓ / 1: 59 descubiertas; runner detenido por fixture run. |
| Mismo comando tras renombrar fixture | PASÓ / 0: Ran 59 tests in 1.604s, OK. |
| bash scripts/verify-modelos.sh antes de versionar | PASÓ / 0: construcción, fuentes, dependencias, check, migrate, comprobación de migraciones y 63 pruebas; Ran 63 tests in 1.654s, OK. |
| docker run --rm catalogo-modelos-201907608-modelos python --version | Python 3.13.16 / 0. |
| docker compose -f compose.modelos.yaml exec -T db postgres --version | PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2) / 0. |
| bash -n scripts/verify-modelos.sh | Sintaxis Bash válida / 0. |
| git diff --check | Sin errores de espacios en los cambios rastreados / 0. |

Se comprobó sintaxis de 21 archivos iniciales con ast sin ejecutar el dominio
(código 0), y posteriormente todos los Python. Los enlaces locales de doce
documentos Markdown se comprobaron sin enlaces rotos (código 0). Se compararon
hashes de originales al iniciar y dentro de la rutina. Las cuatro regresiones
adicionales comprueban normalización directa de identificador, procedencia
histórica después de cambiar el código de un servicio y los CHECK locales de
sección manual/origen válido. La ejecución contra commit se añadirá al completar.

## Cobertura de los trece controles mínimos solicitados

Todos son métodos de ModelIntegrityTests en tests/test_models.py. Los 63 tests
incluyen estos controles; los subTest de un método no aumentan esa cifra.

| Control mínimo | Método test_ correspondiente |
|---|---|
| 1. Empresa duplicada | empresa_codigo_duplicado_rechazado |
| 2. Área duplicada dentro de empresa | area_codigo_duplicado_mismo_padre_rechazado |
| 3. Mismo código de área en otra empresa | area_codigo_mismo_otro_padre_permitido |
| 4. Departamento sin área | departamento_sin_area_rechazado |
| 5. Sección sin departamento | seccion_sin_departamento_rechazada |
| 6. Puesto sin sección | puesto_sin_seccion_rechazado |
| 7. Empresa derivada de usuario | empresa_usuario_derivada_sin_columna_redundante |
| 8. N2 sin N1 | servicio_n2_sin_n1_rechazado |
| 9. Mínimo mayor que máximo | minimo_mayor_maximo_creacion_rechazado y minimo_mayor_maximo_edicion_rechazado |
| 10. Umbral NULL | umbrales_null_permitidos_y_conservados |
| 11. Responsable de misma sección | responsable_misma_seccion_aceptado |
| 12. Responsable de otra sección | responsable_otra_seccion_rechazado |
| 13. Asociación nueva a padre inactivo | relaciones_a_padres_inactivos_rechazadas |

Cobertura adicional: hash/normalización/roles, obligatoriedad de puesto,
unicidad de servicios y unidades, estado desconocido, catálogos inactivos,
bajas bloqueadas, históricos, reactivación, traslados, APIs masivas rechazadas,
guardado parcial, revisiones manuales, constraints SQL y evidencia de origen.

Cuatro migraciones 0001_initial: organization, accounts, catalog e imports;
Usuario está en la primera migración de accounts, con organización como
dependencia. El esquema añade 17 constraints nombrados (5 UNIQUE y 12 CHECK),
además de 7 campos unique, NOT NULL, FK y no negatividad de contadores.

## Fallos y correcciones conservados

Fallo no deliberado 1: al escribir Dockerfile desde una cadena, una continuación
de línea se convirtió en un + literal. Extracto:

~~~text
ERROR: Invalid requirement: '+'
failed to solve ... exit code: 1
~~~

Causa/corrección: línea RUN mal formada; separar pip install y useradd en dos
RUN. El mismo comando de construcción terminó en 0. No cambió el stack.

Fallo no deliberado 2: fixture cls.run guardaba una EjecucionImportacion,
ocultando unittest.TestCase.run. Extracto:

~~~text
TypeError: 'EjecucionImportacion' object is not callable
~~~

Corrección: cls.ejecucion/self.ejecucion. No eliminar tests, aserciones ni casos;
repetir el mismo comando. Los 59 escenarios pasaron. Esto registra el ciclo
real tarea → cambio IA → control → fallo → corrección → ejecución satisfactoria;
no es evidencia de una mejora de prompt ni de P01–P12.

## Aislamiento y límites

Pruebas únicamente en test_catalogo_modelos, datos sintéticos y rollback;
--keepdb conserva BD, no se eliminan volúmenes. Bypass save_base en casos
controlados comprueba CHECK/UNIQUE/FK; no es un acceso permitido en negocio.
Las FK diferidas se fuerzan a comprobar dentro de la transacción de prueba.
No se registran contraseñas ni hashes de usuarios. Excel/enunciado se comparan
por SHA-256 y permanecen solo lectura; no se ejecuta importación.
