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

Los resultados finales y el commit probado se añadirán al ejecutar los controles.

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

Los controles finales contra commit identificado se añadirán al terminar las
dos rutinas completas. Ningún resultado está inferido de tener archivos.

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
