# Evidencia de base/modelo — registro de trabajo

Fecha: 2026-10-04, America/Guatemala. Base: f5f39e3.
Este registro documenta comandos reales de esta fase; P01–P12 no se ejecutaron.
Código verificado: d513d949d9ed94c7d7b8e7b4b8ca0ee34ca9fd9e.
Este registro final se añade en un commit documental posterior; el código,
migraciones, dependencias y pruebas permanecen iguales al commit verificado.

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
sección manual/origen válido. El resultado contra commit está registrado abajo.

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

## Verificación del commit de implementación

Commit: d513d949d9ed94c7d7b8e7b4b8ca0ee34ca9fd9e, mensaje
feat: crear base Django y modelos persistentes. git status --porcelain estaba
vacío antes de ejecutar y después de terminar la rutina. Cierre de verificación
y apagado registrado a las 2026-10-04T20:12:39-06:00, America/Guatemala.

Comando ejecutado: bash scripts/verify-modelos.sh. Resultado global: código 0.
Cada paso es secuencial, con set -euo pipefail; cualquier error detiene la rutina.

| Comando real dentro del script (prefijo docker compose -f compose.modelos.yaml) | Resultado / código |
|---|---|
| build modelos | Imagen reconstruida con las fuentes del commit / 0. |
| up -d db | PostgreSQL propio disponible, healthy como dependencia / 0. |
| run --rm modelos python /app/scripts/check_sources.py | Enunciado y Excel: integridad verificada / 0. |
| run --rm modelos python -m pip check | No broken requirements found / 0. |
| run --rm modelos python manage.py check | System check identified no issues (0 silenced) / 0. |
| run --rm modelos python manage.py migrate --noinput | No migrations to apply; las cuatro iniciales ya estaban aplicadas / 0. |
| run --rm modelos python manage.py makemigrations --check --dry-run | No changes detected / 0. |
| run --rm modelos python manage.py test tests --keepdb --verbosity 2 | Found 63 test(s); Ran 63 tests in 1.820s; OK / 0. |

Extracto real de salida final:

~~~text
Ran 63 tests in 1.820s

OK
Preserving test database for alias 'default' ('test_catalogo_modelos')...
~~~

Controles adicionales ejecutados antes de versionar: AST de 30 archivos Python
válido, 63 métodos test_ encontrados, enlaces locales Markdown válidos y
SHA-256 de enunciado/Excel/.gitignore idénticos a los iniciales (código 0).
git diff --cached --check pasó (0) para todos los archivos nuevos/modificados.
Estos controles estáticos no se presentan como pruebas funcionales.

Después: docker compose -f compose.modelos.yaml stop terminó en código 0;
catalogo-modelos-201907608-db-1 quedó Stopped. No se eliminó volumen ni base.
No hubo push, etiqueta final de entrega ni modificación de remoto.

## Archivos y estructura versionados

Modificados: AGENTS.md, docs/DECISIONES.md, docs/MATRIZ_TRAZABILIDAD.md y
docs/REQUISITOS.md. Todos los demás de la siguiente salida son nuevos.
No se modificaron ENUNCIADO.md, data/CatalogoServicios.xlsx ni .gitignore.
V1 y PROMPT-01 conservan sus versiones históricas.

Salida real de git diff --stat f5f39e3 d513d94:

~~~text
 .dockerignore                               |  20 ++
 .env.example                                |  10 +
 AGENTS.md                                   |  78 +++--
 Dockerfile.modelos                          |  12 +
 README.md                                   |  67 ++++
 compose.modelos.yaml                        |  45 +++
 docs/DECISIONES.md                          |  61 ++--
 docs/MATRIZ_TRAZABILIDAD.md                 |  40 ++-
 docs/MODELO_DATOS.md                        |  94 ++++++
 docs/REQUISITOS.md                          |   2 +-
 docs/contexto/CONTEXTO_V2.md                |  76 +++++
 docs/evidencias/FASE_MODELO.md              | 104 ++++++
 docs/prompts/P02_MODELO.md                  |  72 +++++
 requirements.txt                            |  14 +
 scripts/check_sources.py                    |  14 +
 scripts/verify-modelos.sh                   |  12 +
 src/accounts/__init__.py                    |   0
 src/accounts/apps.py                        |   6 +
 src/accounts/migrations/0001_initial.py     |  46 +++
 src/accounts/migrations/__init__.py         |   0
 src/accounts/models.py                      | 132 ++++++++
 src/catalog/__init__.py                     |   0
 src/catalog/apps.py                         |   6 +
 src/catalog/migrations/0001_initial.py      | 112 +++++++
 src/catalog/migrations/__init__.py          |   0
 src/catalog/models.py                       | 133 ++++++++
 src/config/__init__.py                      |   0
 src/config/domain.py                        | 197 ++++++++++++
 src/config/settings.py                      |  99 ++++++
 src/config/settings_test.py                 |  12 +
 src/config/urls.py                          |   2 +
 src/config/wsgi.py                          |   6 +
 src/imports/__init__.py                     |   0
 src/imports/apps.py                         |   6 +
 src/imports/migrations/0001_initial.py      | 115 +++++++
 src/imports/migrations/__init__.py          |   0
 src/imports/models.py                       | 173 ++++++++++
 src/manage.py                               |  10 +
 src/organization/__init__.py                |   0
 src/organization/apps.py                    |   6 +
 src/organization/migrations/0001_initial.py | 125 ++++++++
 src/organization/migrations/__init__.py     |   0
 src/organization/models.py                  |  72 +++++
 tests/__init__.py                           |   0
 tests/test_models.py                        | 474 ++++++++++++++++++++++++++++
 45 files changed, 2395 insertions(+), 58 deletions(-)
~~~

El commit documental posterior solo agrega este registro final. Su identidad
se obtiene con git log -1 --format='%H %s' -- docs/evidencias/FASE_MODELO.md.
Para el acumulado final: git diff --stat f5f39e3 HEAD.

## Pendientes de la siguiente fase

Implementar lector/importador y comparación de reimportación, autenticación y
roles HTTP, interfaz de mantenimientos/consulta, demo, Docker final y P01–P12.
Completar segunda actualización de contexto por otro hallazgo real, tres
prompts mínimos adicionales, dos mejoras de prompt, metadatos exactos de IA,
README/RESOLUCION finales y verificación de entrega/acceso GitHub.
El esquema y sus límites están en MODELO_DATOS; la cobertura parcial y tareas
futuras están en MATRIZ_TRAZABILIDAD. No se declara terminado el proyecto total.
