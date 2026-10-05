# Matriz de trazabilidad — fase funcional

Fecha: 2026-10-04. Requisitos: [REQUISITOS.md](REQUISITOS.md).
Decisiones: [DECISIONES.md](DECISIONES.md).

La tabla de cobertura actual distingue modelo de aceptación funcional. La
matriz posterior conserva criterios del plan. P01–P11 automatizadas y probadas;
P06–P08 conservan aprobación previa. P12 sigue pendiente. Un test de modelo
no completa un P; los nuevos escenarios comprueban peticiones HTTP.

## Cobertura actual parcial

| Requisito | Implementación real | Control interno / estado |
|---|---|---|
| A01–A05 | accounts/forms.py/access.py, config/urls.py/web.py y templates | Login/logout, Argon2id, sesiones/inactivos, roles/CSRF probados en HTTP. P01–P03. |
| O01–O03 | organization/models.py, UsuarioForm y mantenimientos web | Jerarquía, unicidad, referencias, empresa derivada y seis CRUD/bajas probados. P04/P05. |
| O04 | config/domain.py y desactivar() mediante web | Dependientes activos/desconocidos bloqueados e históricos conservados en HTTP. |
| C01/C02/C03 | catalog/forms.py, mantenimientos y templates | N1/N2/tres clasificaciones mantenibles; referencias controladas y Demostration conservado. |
| C04/C07 | ServicioForm y dominio existente | Umbrales/responsables/movimientos probados por HTTP, P09/P11; demo tres asignaciones. |
| C05/C06 | ServiceFilters, list/detail y paginación | Código/nombre, cinco filtros, combinaciones/páginas y ficha completa probados. P10. |
| I01–I08 | imports/services y comando import_catalog | 12/46, repetición, SE.12/NULL, filas 42/67, opciones, trazabilidad y divergencias probados; P06–P08 aprobadas. |
| IA01/IA02 | AGENTS V3, CONTEXTO_V2/V3 | Dos actualizaciones por hallazgos reales; V1 histórico. |
| IA03/IA04 | P01_ANALISIS/P02_MODELO/P03_IMPORTACION/P04_AUTENTICACION_FUNCIONAL y dos revisiones | Cuatro temas y dos mejoras reales comprobadas; quinto tema y metadatos exactos pendientes. |
| H01/H02/H04 | verify-funcional.sh, verify-web-local.sh y probe_funcional.py, además de harness previo | Pruebas dirigidas, suite completa y HTTP/CLI reales en BD test_; puerto local verificado, P12 pendiente. |
| D01/D02/D03 | Dockerfile.modelos, compose.modelos.yaml, requirements | Entorno mínimo Python/PostgreSQL reproducible; despliegue final/P12 pendientes. |
| I08/H03 | scripts/check_sources.py y mounts ro | Originales solo lectura y hashes verificados antes/después; P06 aprobada. |

Los resultados y commit probado están en
[FASE_MODELO.md](evidencias/FASE_MODELO.md). Enlaces al esquema y pruebas:
[MODELO_DATOS.md](MODELO_DATOS.md), [tests](../tests/test_models.py).
Evidencia de importación:
[FASE_IMPORTACION.md](evidencias/FASE_IMPORTACION.md).
Evidencia funcional: [FASE_FUNCIONAL.md](evidencias/FASE_FUNCIONAL.md).

## Aceptación cerrada en esta fase

| Requisito | Tarea/implementación real | Prueba real | Evidencia |
|---|---|---|---|
| I01/I02/I06/I08/C02 | T07–T10 parser/normalizer/importer/traceability, import_catalog | test_P06_importar_original: 12 N1/46 N2, opciones, incidencias y origen. | FASE_IMPORTACION, comando/fecha/commit. |
| I01/I07 | Reconciliación PD06/D14 y ejecución nueva | test_P07_repetir_importacion: cero duplicados/cambios silenciosos, 152 orígenes. | Primera/segunda y contadores reales. |
| I03/I04/I05/I07 | Canónico SE.12, texto exacto, inferencia y NULL | test_P08_se12_y_ausencias | Ambos nombres/coordenadas, transformación C101 y ausencias. |
| D10/PD06 | Baseline IMPORTADO y comparación por campo | tests de segunda/tercera reimportación, fuente nueva y edición humana. | Suite de persistencia y snapshots. |
| H02/H03 | BD test_ y demostración CLI nueva; nunca reset normal | probe_importacion.py y checks hash | Nombre de base conservada, salidas/códigos y hashes. |

## Aceptación funcional nueva

Métodos de OfficialWebAcceptanceTests en tests/test_web_acceptance.py; todos
usan PostgreSQL test_ y peticiones HTTP a través de middleware/vistas/templates.
Comando, fecha, fallos/correcciones y commit probado en FASE_FUNCIONAL.

| Requisito | Implementación | Prueba identificada | Evidencia |
|---|---|---|---|
| A01/A02 | LoginView/LocalAuthenticationForm/hasher existente | P01 login válido normalizado e inválido. | Acceso y sesión correctos, rechazo sin login. |
| A03/A05 | Guarda común/LogoutView/ModelBackend | P02 anónimo, logout/cookie antigua e inactivo. | Sesión invalidada; reactivación no recupera cookie previa. |
| A04 | functional_access(write=True) y menú según rol | P03 consulta lee y peticiones directas rechazan escritura. | 403, estado persistido intacto; todas las rutas con regresión adicional. |
| O01/O02 | ModelForms y mantenimientos de seis entidades | P04 crear jerarquía completa y usuario por HTTP. | Relaciones recuperables/empresa derivada. |
| O03 | Formularios/constraints/dominio | P05 duplicado y FK inexistente. | Mensajes comprensibles y ningún dato inválido persistido. |
| C04 | ServicioForm/ServicioNivel2.clean | P09 crear/editar mínimo > máximo. | Formulario con error, valores previos intactos. |
| C05/C06 | ServiceFilters/listado/ficha | P10 código/nombre, cinco filtros, combinación, NULL y páginas. | Resultados/páginas coherentes. |
| C07 | Referencias controladas/dominio de responsables | P11 otra sección rechazado, misma sección aceptado. | Datos válidos recuperados. |
| A06/C07 | seed_demo transaccional | Siete tests demo y dos CLI reales. | Dos roles/tres asignaciones; repetición sin nuevas entidades ni sobrescrituras. |
| O01/O04/C03 | Mantenimientos reutilizados | Cinco tests CRUD y 19 de seguridad HTTP. | Altas/edición/bajas sin borrado, traslados protegidos, todos los formularios. |

P06–P08 se ejecutan como regresiones, sin presentarlas como pruebas nuevas.

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
T04/T16 limitados al entorno interno y perfil web local. T07–T15 implementados
y probados. T20 incluye V3, cuatro temas y dos revisiones reales; no cierre
final de IA/documentación. Solo T17/P12, despliegue final, documentación y entrega
permanecen pendientes.

## Requisito → futura implementación → futura prueba → futura evidencia

P = prueba obligatoria; VC = control complementario; VD = verificación documental.
La tabla conserva el plan normativo: P01–P11 remiten al cierre real anterior;
P12 y requisitos de entrega/IA aún incompletos conservan criterios pendientes.

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
| IA03 | T20 prompts | VD cinco usados con todos los campos y temas obligatorios. | Cuatro temas registrados; pruebas/Docker y versión exacta pendientes. |
| IA04 | T20 mejoras | VD dos iteraciones con problema y resultados reales; metadatos. | P03 integridad/P04 sesiones comprobadas; metadatos exactos pendientes. |
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
Separar control documental de prueba funcional: P01–P11 tienen controles reales;
P12 queda pendiente. Tener un plan o detener contenedores no aprueba P12.
No copiar credenciales, hashes de contraseña ni conversaciones completas.
