# Evidencia de la fase de importación

Fecha: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo/versión exacta: PENDIENTE DE REGISTRAR MANUALMENTE.
Base: b08a1e5432b71e744743b0f966376d15abaa7f1d.
Rama inicial: main; árbol inicial limpio; origin:
https://github.com/Ahletz/parcial-catalogo-servicios-201907608.git.
No modificar remoto ni ejecutar push/tag/rebase/merge/reset.

## Integridad inicial

ENUNCIADO.md:
c99201ed3e60aadbed9c7bebbfcc970290e6d13287eec0cbac984d01a0d55cfa.
data/CatalogoServicios.xlsx:
de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0.
Comando: sha256sum ENUNCIADO.md data/CatalogoServicios.xlsx; código 0.

## Resultado antes de editar código

Comando: bash scripts/verify-modelos.sh, sobre la base indicada.
Resultado: código 0; fuentes íntegras, pip check y Django check sin problemas,
migraciones aplicadas sin pendientes y makemigrations sin cambios.

~~~text
Ran 63 tests in 2.832s

OK
Preserving test database for alias 'default' ('test_catalogo_modelos')...
~~~

Fuentes leídas completas: AGENTS, ENUNCIADO, V1, V2, REQUISITOS, ANALISIS_EXCEL,
DECISIONES, MODELO_DATOS y MATRIZ; modelos/migraciones inspeccionados. Excel:
relectura ZIP/XML solo de datos para comprobar cabeceras y filas relevantes.
Nuevas decisiones D14–D18 concretadas antes de implementar.

Los resultados finales contra el commit de implementación están registrados en
la sección «Verificación final» de este documento.

## Fallos reales durante desarrollo

1. Comprobación AST del lector/tests y comando
   docker compose -f compose.modelos.yaml run --rm modelos python manage.py test
   tests.test_import_parser --keepdb --verbosity 2 fallaron (código 1):

~~~text
SyntaxError: bytes can only contain ASCII literal characters
~~~

Causa: fixture de libro corrupto usó un literal bytes con acento. Corrección:
texto Unicode codificado explícitamente con encode("utf-8"); mismo contenido,
casos y aserciones. No era un fallo deliberado ni una mejora de prompt.
Se repetirán ambos controles y se conservará su resultado real.

Repetición: AST código 0; el mismo comando del lector pasó con 37 pruebas en
31.141s, código 0. Se añadió después un control de límites de opciones y se
indexaron rangos para resolverlos sin búsqueda repetida.

2. Una petición de apply_patch falló en la capa de orquestación JavaScript:
SyntaxError: Invalid or unexpected token. No se llamó la herramienta ni se
modificó archivo. Causa: expansión Bash dentro de template literal JavaScript.
Se usaron comandos Bash explícitos; la petición corregida se aplicó.

3. Comando real:
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test
tests.test_import_parser tests.test_import_persistence --keepdb --verbosity 2.
Resultado código 1: Found 60 test(s), Ran 44 tests in 25.241s,
FAILED (errors=6); setUpClass bloqueó los 16 métodos de persistencia restantes.

~~~text
django.core.exceptions.ValidationError: {'codigo': ['Este valor es obligatorio.']}
~~~

Causa real: IncidenciaImportacion.codigo tiene blank=True; DomainValidationMixin
impone obligatoriedad genérica ignorando ese metadato. Afecta incidencias de
filas sin identidad y también el registro posterior del fallo fatal. No
inventar códigos ni eliminar aserciones; corregir validación heredada para
respetar campos opcionales. Es un hallazgo concreto para CONTEXTO_V3.
La revisión de instrucciones de trabajo queda en P03_REVISION_INTEGRIDAD.
La repetición posterior se registra a continuación.

Repetición del MISMO comando después del ajuste: código 0, Ran 60 tests in
46.420s, OK. No se quitaron tests ni aserciones. La prueba de rollback tiene un
fallo sintético expresamente declarado, separado del bug real de obligatoriedad.

## Controles satisfactorios anteriores al commit de implementación

| Comando real | Resultado / código |
|---|---|
| AST de todos los Python del proyecto | Válido / 0. |
| bash -n scripts/verify-importacion.sh scripts/verify-modelos.sh | Sintaxis válida / 0. |
| git diff --check | Sin errores de espacios / 0. |
| docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_import_parser tests.test_import_persistence --keepdb --verbosity 2 | 60 tests, 46.420s, OK / 0. |
| docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_import_acceptance --keepdb --verbosity 2 | 3 tests, 8.214s, OK / 0. |
| docker compose -f compose.modelos.yaml run --rm modelos python /app/scripts/probe_importacion.py | Migración y dos CLI reales 0; base test_ nueva conservada / 0. |
| bash scripts/verify-modelos.sh después del ajuste | Fuentes/check/pip/migraciones válidos; 63 tests, 1.750s, OK / 0. |

P06: ejecución 37 en base de pruebas, 76 creados, 12 N1/46 N2/18 opciones,
cuatro observados/cuatro incidencias y 76 orígenes. P07: ejecuciones 38/39,
segunda con cero creados/actualizados y 76 omitidos, 152 orígenes/ocho incidencias.
P08: canónico, dos nombres, códigos exactos, C101 inferido y NULL verificados.
Los IDs de estos tests son temporales y los datos vuelven atrás por TestCase.

Demostración CLI persistente anterior al commit:
test_importacion_evidencia_6fddb74a26ec44368cc1f1b8dbb0ad84.
Ejecuciones 1/2 COMPLETADAS. Primera creó N1=12, N2=46, CLASE=2, CRITICIDAD=5,
TIPO=11; actualizados=0/omitidos=0. Segunda creó/actualizó cero y omitió
12/46/2/5/11 respectivamente. Ambas: observados=4, incidencias=4,
97 filas/49 continuaciones/2 sin identidad. Persistido: dos ejecuciones,
152 orígenes y ocho incidencias. Hash antes/después de Excel:
de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0.

Las dos rutinas completas pasaron después del commit identificado; los tiempos,
códigos y nueva demostración persistente se registran en «Verificación final».
Ningún resultado está inferido de tener archivos.

## Arquitectura, reglas y archivos de esta fase

- imports/management/commands/import_catalog.py: CLI corto y resumen JSON.
- imports/services/parser.py: lectura de los mismos bytes usados en el hash,
  hoja/encabezados, resolución por principal/rango e identificación de filas.
- normalizer.py: selección determinista de candidatos, opciones, S/N/NULL,
  Decimal, SE.12 y prefijo exacto único; no persistencia.
- importer.py: búsqueda de identidad/procedencia, comparación por campo,
  transacción funcional y contadores; protección de cambios humanos.
- traceability.py: celdas originales/tipo/principal/rango, interpretados,
  aplicados, transformaciones, revisión capturada e incidencias persistentes.
- config/domain.py: corrección mínima de campos opcionales; sin cambio de
  campos, modelos, dependencias ni cuatro migraciones iniciales.
- Tests: import_helpers, test_import_parser, test_import_persistence y
  test_import_acceptance. Los 63 tests anteriores permanecen intactos.
- Harness: verify-importacion.sh/probe_importacion.py; verify-modelos ahora
  selecciona explícitamente su módulo. Compose añade mount original ro /app/data.
- Documentación: AGENTS, README, REQUISITOS, ANALISIS_EXCEL, DECISIONES,
  MODELO_DATOS, MATRIZ, CONTEXTO_V3 y dos versiones del prompt de IMPORTACIÓN.

Las combinaciones se indexan y solo propagan dentro de su rango. Se rechazan
rangos que crucen atributos/bloques; no hay forward-fill. Filas 42/67 tienen
incidencia con todo su contenido relevante, sin origen N2 ni vínculo vecino.
SE.12 conserva B99/B100, aplica canónico y registra CONFLICTO_N1. C101 se
asocia por prefijo exacto/único, con transformación e INFERENCIA_N1.
E:L99–101 permanecen NULL. Códigos, nombres, etiquetas y espacios se preservan.
S=True, N=False, ausencia=NULL; Decimal nullable sin cero/round inventados.
Se cargan F/G/H completos, 2/5/11 opciones, incluido Demostration. E112:E113
define mapa booleano guardado como transformación, sin inventar otro catálogo.

RegistroOrigen separa originales/importados/aplicados y ID del registro.
La evidencia de filas incluye coordenadas de las principales utilizadas;
esas coordenadas no atribuyen una fila huérfana a un servicio.
Incidencia guarda categoría/ubicación/valores/regla/resultado. No se agregan
campos ficticios de severidad/revisión que el modelo no tiene.
El estado/fechas/contadores de ejecución expresan su resultado persistido.

## Cobertura de los 26 controles mínimos

| Control | Test correspondiente (prefijo test_) |
|---|---|
| 1. Hoja correcta | lee_hoja_correcta_y_encabezados |
| 2. Archivo inexistente | archivo_inexistente, comando_archivo_inexistente_es_error |
| 3. Hoja inexistente | hoja_inexistente |
| 4. Combinada | resuelve_principal_del_rango |
| 5. Sin propagación externa | no_propaga_fuera_del_rango |
| 6. Continuaciones | clasifica_continuaciones |
| 7. Filas 42/67 | filas_42_y_67_sin_identidad, filas_42_y_67_incidentes_sin_vinculo_servicio |
| 8. Conflicto SE.12 | conflicto_se12_detectado, conflicto_se12_persistente_y_ambos_nombres |
| 9. Canónico | nombre_canonico_se12 |
| 10. Dos nombres | conserva_ambos_nombres_y_coordenadas |
| 11–13. Códigos exactos | se121_texto_exacto, se122_texto_exacto, se123_texto_exacto |
| 14. Inferencia C101 | inferencia_fila_101, inferencia_101_persistente |
| 15. NULL 99–101 | atributos_null_99_a_101 |
| 16–18. S/N/ausencia | activo_s, activo_n, activo_ausente |
| 19. Umbrales nullable | umbrales_nullable_y_cero_diferentes |
| 20. Opciones completas | catalogos_completos_incluidos_no_usados |
| 21. Demostration | demostration_sin_correccion |
| 22. Procedencia | origen_persistido_con_original_interpretado_y_rangos |
| 23. Incidencia | filas_42_y_67_incidentes_sin_vinculo_servicio |
| 24. Idempotencia | idempotencia_entidades_y_nueva_trazabilidad |
| 25. Modificación humana | edicion_humana_protegida_en_segunda_y_tercera_importacion |
| 26. Solo datos | texto_con_codigo_aparente_solo_se_almacena |

Niveles: 38 tests puros SimpleTestCase, 22 de integración/persistencia TestCase,
tres oficiales TestCase y 63 anteriores de modelo. Total 126 escenarios únicos;
repeticiones durante corrección/finales no se cuentan como nuevos escenarios.

## Limitaciones y pendientes

Contrato fijo de hoja/encabezados/bloques del original. Fórmulas rechazadas;
no se interpretan caches, macros ni órdenes. Decimal(20,6) no se redondea:
fuentes con mayor precisión fallan y revierten. El lock serializa escrituras.
Si PostgreSQL deja de ser accesible, puede impedir registrar el propio fallo.
Un proceso terminado abruptamente puede dejar ejecución EJECUTANDO; recuperación
de procesos interrumpidos no está implementada. No hay inferencia automática de
renombres en la nueva fuente; se protege el renombre humano con ID de origen.
Cada probe conserva nueva BD test_, sin borrar otras bases ni volúmenes.
La evidencia se consulta por ORM/CLI; vistas de trazabilidad son futuras.

P01–P05/P09–P12, auth/roles HTTP, UI/demo, Docker final/persistencia P12,
README/RESOLUCION finales y entrega/acceso GitHub siguen pendientes.
V3 es segunda actualización real; tres temas de prompts y una revisión usados.
Faltan autenticación/pruebas-Docker y otra mejora real; versión exacta de IA
no expuesta y pendiente de registrar. No hubo push ni tag ni lectura de secretos.

## Verificación final

Terminada el 2026-10-04T21:30:06-06:00, America/Guatemala.
Commit de código probado: 628efa5e846f01a20bf9d3775eacbe4262f862c9.
Mensaje: feat: importar catalogo Excel con trazabilidad e idempotencia.
Las dos rutinas se ejecutaron sobre ese commit con el árbol limpio, sin editar
archivos mientras corrían. La imagen construida/reutilizada fue
b3ef738bbd1e2a171c24227b81f369e60d668d56ee29d89c28c466a03382d8c0.

| Control final real | Resultado | Código |
|---|---|---|
| bash scripts/verify-modelos.sh | 63 tests en 1.741s, OK; regresiones conservadas. | 0 |
| bash scripts/verify-importacion.sh | Construcción, controles, 60 tests, P06/P07/P08 y dos CLI reales satisfactorios. | 0 |
| python -m pip check, en cada rutina | No broken requirements found. | 0 |
| python manage.py check, en cada rutina | System check identified no issues (0 silenced). | 0 |
| python manage.py migrate --noinput, en cada rutina | No migrations to apply. | 0 |
| python manage.py makemigrations --check --dry-run, en cada rutina | No changes detected. | 0 |
| tests.test_import_parser y tests.test_import_persistence | Ran 60 tests in 48.377s, OK. | 0 |
| P06, invocación individual del harness | Ran 1 test in 2.351s, OK; original 12/46, 18 opciones, cuatro incidencias y 76 orígenes. | 0 |
| P07, invocación individual del harness | Ran 1 test in 3.794s, OK; segunda ejecución sin creados/actualizados y sin duplicados. | 0 |
| P08, invocación individual del harness | Ran 1 test in 2.174s, OK; canónico, ambos nombres, códigos, inferencia y NULL. | 0 |
| check_sources.py, al principio/final del harness | ENUNCIADO.md y CatalogoServicios.xlsx: integridad verificada. | 0 |
| probe_importacion.py | Nueva BD aislada; migraciones y dos comandos import_catalog reales con códigos 0/0/0. | 0 |

Son 126 métodos de prueba distintos ejecutados satisfactoriamente en los
controles finales: 63 modelos + 38 lector/normalización + 22 persistencia +
P06 + P07 + P08. Los controles auxiliares y las importaciones CLI no aumentan
ese número. Ningún fallo quedó pendiente; los fallos previos se conservan arriba.

Los IDs P06=66 y P07=67/68 corresponden a TestCase sobre test_catalogo_modelos;
sus cambios se revierten. La evidencia persistente siguiente es independiente.

### Primera y segunda importación CLI final, persistidas

Base nueva conservada:
test_importacion_evidencia_830e4b473a2e4d8a96ed3c2e45aea7c4.
Migraciones: código 0. Comando en ambas ejecuciones:

~~~bash
python manage.py import_catalog --file /app/data/CatalogoServicios.xlsx
~~~

El probe define DB_NAME para esa base test_ antes de inicializar Django; nunca
importa en catalogo_modelos ni en una base funcional/de evaluación.

| Entidad | Primera: creados / actualizados / omitidos | Segunda: creados / actualizados / omitidos | Cantidad final |
|---|---|---|---|
| Nivel 1 | 12 / 0 / 0 | 0 / 0 / 12 | 12 |
| Nivel 2 | 46 / 0 / 0 | 0 / 0 / 46 | 46 |
| Clase | 2 / 0 / 0 | 0 / 0 / 2 | 2 |
| Criticidad | 5 / 0 / 0 | 0 / 0 / 5 | 5 |
| Tipo | 11 / 0 / 0 | 0 / 0 / 11 | 11 |
| Total funcional | 76 / 0 / 0 | 0 / 0 / 76 | 76 |

Ejecuciones 1 y 2: COMPLETADA, código de cada comando 0. Cada una reporta
cuatro observados/cuatro incidencias: dos filas sin identidad, conflicto N1 y
asociación N2 inferida. Observados es un contador de casos que requieren revisión;
no constituye una partición adicional de creados/actualizados/omitidos.
Cada ejecución analiza 97 filas: 46 servicios explícitos, 49 continuaciones,
dos sin identidad y cero vacías. Persistido después de ambas:
dos EjecucionImportacion COMPLETADAS, 152 RegistroOrigen y ocho IncidenciaImportacion.
La segunda no altera entidades funcionales; añade su propia evidencia.

### Hashes iniciales y finales

sha256sum ENUNCIADO.md data/CatalogoServicios.xlsx .gitignore, código 0,
después de las dos rutinas. Valores iniciales = finales:

~~~text
ENUNCIADO.md
antes:   c99201ed3e60aadbed9c7bebbfcc970290e6d13287eec0cbac984d01a0d55cfa
después: c99201ed3e60aadbed9c7bebbfcc970290e6d13287eec0cbac984d01a0d55cfa
data/CatalogoServicios.xlsx
antes:   de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0
después: de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0
.gitignore
antes:   5d1b373b93f09538b2c0d39a905d7c472dca2db00225beec797cb1c6074530a7
después: 5d1b373b93f09538b2c0d39a905d7c472dca2db00225beec797cb1c6074530a7
~~~

### Inventario y commits

19 archivos nuevos y 10 modificados en el commit de implementación.
Salida real de git diff --stat b08a1e5 628efa5:

~~~text
 AGENTS.md                                         |  53 +++--
 README.md                                         |  70 +++++-
 compose.modelos.yaml                              |   3 +-
 docs/ANALISIS_EXCEL.md                            |  11 +-
 docs/DECISIONES.md                                |  77 ++++++-
 docs/MATRIZ_TRAZABILIDAD.md                       |  45 ++--
 docs/MODELO_DATOS.md                              |   6 +-
 docs/REQUISITOS.md                                |   6 +-
 docs/contexto/CONTEXTO_V3.md                      |  84 +++++++
 docs/evidencias/FASE_IMPORTACION.md               | 198 +++++++++++++++++
 docs/prompts/P03_IMPORTACION.md                   |  84 +++++++
 docs/prompts/P03_REVISION_INTEGRIDAD.md           |  44 ++++
 scripts/probe_importacion.py                      | 103 +++++++++
 scripts/verify-importacion.sh                     |  17 ++
 scripts/verify-modelos.sh                         |   2 +-
 src/config/domain.py                              |   9 +-
 src/imports/management/__init__.py                |   0
 src/imports/management/commands/__init__.py       |   0
 src/imports/management/commands/import_catalog.py |  22 ++
 src/imports/services/__init__.py                  |   0
 src/imports/services/exceptions.py                |   6 +
 src/imports/services/importer.py                  | 229 ++++++++++++++++++++
 src/imports/services/normalizer.py                | 249 +++++++++++++++++++++
 src/imports/services/parser.py                    | 181 ++++++++++++++++
 src/imports/services/traceability.py              |  52 +++++
 tests/import_helpers.py                           |  40 ++++
 tests/test_import_acceptance.py                   | 100 +++++++++
 tests/test_import_parser.py                       | 238 ++++++++++++++++++++
 tests/test_import_persistence.py                  | 253 ++++++++++++++++++++++
 29 files changed, 2113 insertions(+), 69 deletions(-)
~~~

El commit de cierre documental solo actualiza este archivo con resultados
observados; no altera el código probado. Su mensaje identifica el propósito:
docs: registrar verificacion final de importacion. Se obtiene su hash sin
atribuir a un commit su propio hash antes de existir:

~~~bash
git log -1 --format='%H %s' -- docs/evidencias/FASE_IMPORTACION.md
git diff --stat b08a1e5 HEAD
git status --short --branch
git log --oneline --decorate -10
~~~

Al terminar los controles, git status indicó árbol limpio en main y
origin/main [gone] como referencia local de seguimiento ausente; no se consultó
el remoto. Docker compose -f compose.modelos.yaml stop terminó con código 0.
Se conservan el contenedor detenido, volumen y bases; no se ejecutó down -v,
DROP ni borrado de archivos. README documenta consulta ORM de la evidencia.
Los límites y pendientes de la fase siguen siendo los indicados arriba.
