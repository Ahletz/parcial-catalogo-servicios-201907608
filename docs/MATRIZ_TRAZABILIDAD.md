# Matriz de trazabilidad — fase de importación

Fecha: 2026-10-04. Requisitos: [REQUISITOS.md](REQUISITOS.md).
Decisiones: [DECISIONES.md](DECISIONES.md).

La tabla de cobertura actual distingue modelo de aceptación funcional. La
matriz posterior conserva tareas/criterios FUTUROS restantes. P06–P08 ya se
ejecutaron/aprobaron; P01–P05/P09–P12 pendientes. Un test de modelo no completa un P.

## Cobertura actual parcial

| Requisito | Implementación real | Control interno / estado |
|---|---|---|
| A02 | accounts/models.py y hasher en config/settings.py | Hash Argon2id y rechazo de texto plano probados; login HTTP pendiente. |
| O02/O03 | organization/models.py, accounts/models.py y migraciones | Jerarquía, unicidad, huérfanos, padres inactivos y empresa derivada probados. P04/P05 pendientes. |
| O04 | config/domain.py y desactivar() | Dependientes activos/desconocidos bloqueados, históricos conservados; UI pendiente. |
| C01/C02 | catalog/models.py, imports/services | Campos/relaciones/etiquetas únicas; 18 opciones originales cargadas en PostgreSQL de pruebas, incluido Demostration. UI pendiente. |
| C04/C07 | catalog/models.py, Usuario/Puesto.clean | Umbrales/responsables/movimientos probados, incluidos CHECK SQL; P09/P11 y demo pendientes. |
| I01–I08 | imports/services y comando import_catalog | 12/46, repetición, SE.12/NULL, filas 42/67, opciones, trazabilidad y divergencias probados; P06–P08 aprobadas. |
| IA01/IA02 | AGENTS V3, CONTEXTO_V2/V3 | Dos actualizaciones por hallazgos reales; V1 histórico. |
| IA03/IA04 | prompts/P01_ANALISIS, P02_MODELO, P03_IMPORTACION y revisión | Tres temas usados; una revisión de importación comprobada; faltan autenticación/pruebas y otra mejora. |
| H01/H02/H04 | verify-modelos.sh, verify-importacion.sh, probe_importacion.py | Rutinas aisladas, fallos/correcciones reales y CLI repetida; harness final HTTP/persistencia pendiente. |
| D01/D02/D03 | Dockerfile.modelos, compose.modelos.yaml, requirements | Entorno mínimo Python/PostgreSQL reproducible; despliegue final/P12 pendientes. |
| I08/H03 | scripts/check_sources.py y mounts ro | Originales solo lectura y hashes verificados antes/después; P06 aprobada. |

Los resultados y commit probado están en
[FASE_MODELO.md](evidencias/FASE_MODELO.md). Enlaces al esquema y pruebas:
[MODELO_DATOS.md](MODELO_DATOS.md), [tests](../tests/test_models.py).
Evidencia de importación:
[FASE_IMPORTACION.md](evidencias/FASE_IMPORTACION.md).

## Aceptación cerrada en esta fase

| Requisito | Tarea/implementación real | Prueba real | Evidencia |
|---|---|---|---|
| I01/I02/I06/I08/C02 | T07–T10 parser/normalizer/importer/traceability, import_catalog | test_P06_importar_original: 12 N1/46 N2, opciones, incidencias y origen. | FASE_IMPORTACION, comando/fecha/commit. |
| I01/I07 | Reconciliación PD06/D14 y ejecución nueva | test_P07_repetir_importacion: cero duplicados/cambios silenciosos, 152 orígenes. | Primera/segunda y contadores reales. |
| I03/I04/I05/I07 | Canónico SE.12, texto exacto, inferencia y NULL | test_P08_se12_y_ausencias | Ambos nombres/coordenadas, transformación C101 y ausencias. |
| D10/PD06 | Baseline IMPORTADO y comparación por campo | tests de segunda/tercera reimportación, fuente nueva y edición humana. | Suite de persistencia y snapshots. |
| H02/H03 | BD test_ y demostración CLI nueva; nunca reset normal | probe_importacion.py y checks hash | Nombre de base conservada, salidas/códigos y hashes. |

## Tareas futuras

| Fase | Tareas |
|---|---|
| F0 Contexto | T01 registrar contexto/requisitos; T02 cerrar decisiones y modelo conceptual. |
| F1 Base | T03 crear Django/usuario personalizado; T04 Docker, configuración, dependencias y estáticos. |
| F2 Modelo | T05 organización/usuarios/clasificaciones/migraciones; T06 N1/N2, responsables, restricciones y procedencia. |
| F3 Importación | T07 lector/clasificación; T08 reglas del Excel; T09 transacciones/idempotencia/reporte; T10 pruebas importación. |
| F4 Funcionalidad | T11 auth/roles; T12 organización/bajas; T13 catálogo/filtros/fichas; T14 demo; T15 pruebas funcionales. |
| F5 Harness | T16 preparación/calidad/pruebas aisladas; T17 P12; T18 ciclo de corrección. |
| F6 Documentación | T19 README/RESOLUCION; T20 contexto/prompts/evidencias/matriz. |
| F7 Entrega | T21 clon limpio/recorrido; T22 acceso GitHub/commit/etiqueta/entrega. |

T02 queda resuelto como diseño; T03/T05/T06 implementados para modelo;
T04/T16 limitados al entorno interno. T20 tiene V1/V2 y dos prompts, no cierre
final de IA/documentación. T07–T10 implementados/probados. T11–T15 funcionales y
P01–P05/P09–P12 pendientes; T20 ahora incluye V3, IMPORTACIÓN y una revisión.

## Requisito → futura implementación → futura prueba → futura evidencia

P = prueba obligatoria; VC = control complementario propuesto; VD = verificación
documental/operativa futura. Filas P06–P08 remiten al cierre real anterior;
las demás conservan criterios pendientes.

| Requisito | Tarea / implementación prevista | Prueba o control esperado | Evidencia futura |
|---|---|---|---|
| A01 | T11 accounts login/logout | P01 válido accede; inválido se rechaza. | Resultado P01 con comando/fecha/commit. |
| A02 | T11 hasher Argon2id | VC hash especializado/sal, no texto plano ni exposición. | Resultado sin imprimir hash ni contraseña. |
| A03, A05 | T11 protección/estado/sesión | P02 sin sesión, logout con cookie anterior e inactivo; sesión previa también rechazada. | Resultado P02 y comprobación de no escritura. |
| A04 | T11 roles y vistas | P03 consulta lee; peticiones directas de modificación rechazadas. | Resultado P03, respuestas sin secretos. |
| A06 | T14 comando demo | VC ambos roles creados de forma repetible con configuración local. | README y resultado sin credenciales reales. |
| O01, O02 | T05/T12 organization/accounts | P04 jerarquía y usuario recuperables; VC altas/edición/bajas de seis entidades. | Resultado P04 y recorrido UI. |
| O03, C01 | T05/T06 unicidad y FK | P05 duplicado/referencia inexistente rechazados. | Resultado P05, errores comprensibles. |
| O03 | T05/T12 reglas de padres | VC sin huérfanos/padres inactivos; mismo código bajo otro padre válido. | Resultados integración y restricciones. |
| O04 | T12 desactivación | VC bloqueo de dependencias activas y conservación histórica. | Prueba por entidad y política RESOLUCION. |
| C01, C03 | T06/T13 servicios | VC mantenimiento N1/N2, todos los campos y referencias válidas. | Resultados y ficha/UI. |
| C02 | T05/T13 clasificaciones | VC mantener catálogos/opciones; etiquetas originales y solo referencias válidas. | Resultados, mapeo y formularios. |
| C04 | T06 validación umbrales | P09 creación y edición mínimo > máximo no guardan; VC igualdad/NULL. | Resultado P09 y datos persistidos. |
| C05 | T13 consulta | P10 código/nombre y filtros N1/estado/clase/criticidad/tipo, combinación y paginación coherentes. | Resultado P10 y recorrido UI. |
| C06 | T13 ficha | VC todos los atributos, ausencias y relación N1 visibles. | Prueba de vista y evidencia seleccionada UI. |
| C07 | T06/T13 responsable | P11 otra sección rechazada; VC sección válida y usuario opcional. | Resultado P11 y asignación válida. |
| C07, O02 | T12 movimientos | VC traslado de usuario/puesto no invalida asignaciones existentes. | Resultado integración. |
| C07, A06 | T14 seed_demo | VC al menos tres asignaciones válidas, ambos roles; repetición sin pisar cambios. | Resultado seed y README. |
| I01, I02, I06, I08 | T07–T10 imports | P06 original: 12 N1/46 N2, combinaciones/opciones/incidencias. | Reporte original con hash y resultado P06. |
| I01, I07 | T09/T10 reimportación | P07 sin duplicados y con nueva ejecución trazable. | Reportes de ambas ejecuciones y P07. |
| I03, I04, I05 | T08/T10 políticas | P08 SE.12 canónico/evidencia de ambos nombres, códigos textuales y NULL. | P08 e incidencias con coordenadas. |
| I06 | T07/T08 clasificación | VC filas 42/67 sin servicio y 49 continuaciones agrupadas. | Incidencias/contadores del reporte. |
| I07, C01 | T08 prefijo fila 101 | VC SE.12.3 asociado a SE.12 con inferencia explícita y padre único. | Registro de transformación C101. |
| I07 | T08/T09 origen/conflictos | VC todos los importados tienen origen; conflicto controlado N2 reportado. | Registros de origen y regla aplicada. |
| I01, I07 | T09 protección de cambios | VC edición humana posterior conservada ante fuente divergente. | Prueba de reimportación e incidencia. |
| I08, H03 | T10/T16 integridad original | VC SHA-256 sin cambios antes/después; archivo solo lectura. | Hash comparado y configuración de acceso. |
| IA01 | T01/T20 AGENTS/contexto | VD agente puede ubicar fuentes, alcance, reglas y comandos; selección por fase. | V1/V2 existentes; verificación final y commits de entrega pendientes. |
| IA02 | T20 actualizaciones | VD dos cambios por hallazgo, motivos/impactos/commits y regla de confianza. | V2/V3 existen por hallazgos reales; V1 no cuenta como actualización. |
| IA03 | T20 prompts | VD cinco usados con todos los campos y temas obligatorios. | Tres temas registrados; dos futuros y versión exacta pendiente. |
| IA04 | T20 mejoras | VD dos iteraciones con problema y resultados reales; metadatos. | Una revisión P03 real/comprobada; segunda pendiente. |
| H01, H02 | T16 scripts/tests | VC rutina reproducible, datos aislados, 0/no-0 y niveles explicados. | scripts/verify.sh, resultados y documentación. |
| H03 | T01/T16 límites | VC no lectura/publicación de secretos ni destrucción fuera de pruebas. | Instrucciones y controles sin contenido sensible. |
| H04 | T18 ciclo IA | VC fallo observado → corrección → nueva ejecución satisfactoria. | Extractos, diff, comandos/commit; declarar ejercicio si deliberado. |
| D01, D02 | T04/T21 Docker | VC clon limpio construye/arranca con comando requerido, sin runtimes anfitrión. | Dockerfile/Compose y resultado del ensayo. |
| D03 | T04/T17 volumen/dependencias | P12 reinicio sin borrar volumen conserva registro previo; VC arranque espera BD. | Script P12, lecturas antes/después y resultado. |
| D04 | T19/T21 README | VD variables, versiones, URL/puertos, logs, apagado/reinicio/recuperación/pruebas. | README validado desde clon limpio. |
| D05 | T21 independencia de IA | VC recorrido funcional sin claves ni suscripción IA. | Configuración y resultado del recorrido. |
| P01–P12 | T10/T15–T17 tests | Los doce escenarios automatizados, datos aislados y UI revisada. | Resultado individual por ID, comando, fecha y commit. |
| G01 | T22 repositorio | VD fuentes/Excel/migraciones/pruebas/docs incluidos; secretos/dependencias excluidos. | Inventario del commit final. |
| G02 | T22 colaborador | VD acceso suficiente o invitación enviada y pendiente informada. | Constancia seleccionada de acceso/invitación. |
| G03, G04 | T22 entrega | VD URL/nombre/carné/rama/SHA y parcial-v2.0 coinciden; disponibilidad mantenida. | Datos de entrega y referencia Git verificable. |
| DOC01 | T19/T21 README | VD otra persona sigue comandos desde clon limpio. | README y ensayo de reproducción. |
| DOC02, GEN01 | T19/T20/T22 RESOLUCION | VD diez apartados, evidencias reales y comprensión/justificación individual. | RESOLUCION, enlaces y reflexión. |

## Actualización posterior

Sustituir rutas previstas por enlaces a implementación y evidencia reales cuando
existan. Registrar estado por requisito/prueba, comando, fecha y commit probado.
Separar control documental de prueba funcional: solo P06–P08 tienen aprobación;
tener un plan no aprueba los otros nueve.
No copiar credenciales, hashes de contraseña ni conversaciones completas.
