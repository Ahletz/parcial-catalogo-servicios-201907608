# Matriz final de trazabilidad

> Matriz histórica del PP2: interpretar sus P01–P12 como **PP2-P01–PP2-P12**.
> No se renombraron métodos ni se reejecutaron controles. La matriz de la nueva
> tarea, con **SD-P01–SD-P18**, está en [PRUEBAS](PRUEBAS.md); su estado real
> de cierre está en [Cierre Service Desk](#cierre-service-desk-2026-10-29).

Fuente: [REQUISITOS](REQUISITOS.md), ENUNCIADO §1–10. Fecha: 2026-10-04.
Estados: COMPLETO exige evidencia ejecutada/documental real; PENDIENTE MANUAL
separa metadatos/acceso/entrega que el agente no puede confirmar. Las fases
anteriores conservan resultados históricos, no pendientes vigentes.

F = [FASE_FUNCIONAL](evidencias/FASE_FUNCIONAL.md), I =
[FASE_IMPORTACION](evidencias/FASE_IMPORTACION.md), C =
[FASE_CIERRE](evidencias/FASE_CIERRE.md), M =
[FASE_MODELO](evidencias/FASE_MODELO.md). Resultado final de ejecución en C.

## Todos los requisitos

| Requisito | Implementación | Prueba / control | Evidencia | Estado |
|---|---|---|---|---|
| A01 | accounts/forms, config/urls LoginView/LogoutView | P01; HTTP real ambos roles/logout | F/C | COMPLETO |
| A02 | settings Argon2id, Usuario.set_password | test_models hash/sal; no exposición HTTP | M/F/C | COMPLETO |
| A03 | accounts/access functional_access | P02, CSRF y todas las rutas protegidas | F/C | COMPLETO |
| A04 | permisos de servidor y menú por rol | P03, 19 tests seguridad, HTTP consulta 403 | F/C | COMPLETO |
| A05 | guarda de inactivos/SESSION_KEY y logout POST | P02; cookie antigua/reactivación | F/C | COMPLETO |
| A06 | seed_demo y variables DEMO_* | 7 tests demo; CLI repetida 2 roles | F/C/README | COMPLETO |
| O01 | organization/accounts, web/forms/templates | P04 y mantenimiento/bajas de seis entidades | M/F/C | COMPLETO |
| O02 | FK jerarquía/empresa derivada | P04, varios usuarios/puesto, relaciones recuperadas | M/F/C | COMPLETO |
| O03 | uniques/FK y dominio padres activos | P05, mismos códigos en padres diferentes, FK/estado | M/F/C | COMPLETO |
| O04 | desactivar/PROTECT/guarda dependientes | test_models y test_web_maintenance/security | M/F/C/RESOLUCION | COMPLETO |
| C01 | N1/N2 con todos los campos y uniques | P05/P06; esquema/ficha | M/I/F/C | COMPLETO |
| C02 | tres catálogos y referencias ModelChoice | opciones 2/5/11, Demostration, CRUD/rechazo inválidas | I/F/C | COMPLETO |
| C03 | web/Form explícitos/save validado | CRUD N1/N2, obligatorios, bajas y GET sin mutación | F/C | COMPLETO |
| C04 | N2.clean/CHECK/ServicioForm | P09 creación/edición; igualdad/NULL≠0 | M/F/C | COMPLETO |
| C05 | ServiceFilters/lista paginada de 20 | P10 búsquedas/cinco filtros/combinaciones/páginas | F/C | COMPLETO |
| C06 | detail/template todos atributos | test_web_security ficha; HTTP real detalle | F/C | COMPLETO |
| C07 | FK responsables/dominio/seed_demo | P11; traslados protegidos; 3 asignaciones válidas | M/F/C | COMPLETO |
| I01 | import_catalog/importer reconciliación | P06/P07; reimportación 0/0/76 | I/C | COMPLETO |
| I02 | parser combinaciones/celda principal | P06; no propagación externa | I/C | COMPLETO |
| I03 | normalizer canónico SE.12/incidencia | P08 ambos nombres/evidencia coordenadas | I/C | COMPLETO |
| I04 | código texto exacto | P08 SE.12.1/.2/.3 | I/C | COMPLETO |
| I05 | campos nullable/desconocidos | P08 E:L99–101 NULL | I/C | COMPLETO |
| I06 | parser identidad/continuaciones/opciones | filas 42/67 no vinculadas; 49 continuaciones | I/C | COMPLETO |
| I07 | RegistroOrigen/Incidencia/snapshots | P07/P08; conflictos, inferencia, edición humana 2ª/3ª | I/C | COMPLETO |
| I08 | original ro/check_sources/12–46 | P06 y SHA inicial/final | I/C | COMPLETO |
| IA01 | AGENTS, V1/V2/V3, RESOLUCION §7 | lectura por fases y comandos documentados | contextos/commits/RESOLUCION | COMPLETO |
| IA02 | actualizaciones V2/V3 y regla de confianza | full_clean/bypass y optional/baseline/FALLIDA | contextos/decisiones | COMPLETO |
| IA03 | cinco temas P01–P05 usados | objetivo/contexto/instrucciones/restricciones/salida/aceptación | prompts/RESOLUCION §8/C | COMPLETO |
| IA04 | revisiones P03/P04 por fallos reales | mismos tests pasan; tool/fecha/modelo disponible | prompts/I/F; exacta manual | COMPLETO con metadato exacto pendiente |
| H01 | verify.sh/common/P12/probes y AGENTS | rutina preparación/BD/carga/calidad/pruebas | C/README | COMPLETO tras harness final 0 |
| H02 | proyecto/volumen QA y test_catalogo_final | rollback; DB/CLI/HTTP/P12; 0/no-0 | C/RESOLUCION §9 | COMPLETO tras harness final 0 |
| H03 | límites AGENTS, ro, configuración pública | hashes; no .env real; no down -v/drop | C | COMPLETO |
| H04 | ciclos errores→correcciones reales | fixture run, optional, sesión/red con repetición | M/I/F/C | COMPLETO |
| D01 | Dockerfile/compose/.dockerignore/.env.example | build desde fuentes fijadas | C/README | COMPLETO tras ensayo limpio |
| D02 | db healthy/init antes web, procesamiento Docker | up --build -d; CLI/contenedores | C/README | COMPLETO tras ensayo limpio |
| D03 | volumen/healthchecks | P12 IDs nuevos, mismo dato y volumen | C | COMPLETO tras P12 final |
| D04 | README comandos/config/logs/stop/up/recuperación | lectura y ensayo limpio, destructivo separado | C/README | COMPLETO |
| D05 | sin proveedor IA para runtime | HTTP/CLI sin claves IA | C/configuración | COMPLETO |
| GEN01 | trabajo individual/decisiones/reflexión | comprensión a defender en evaluación | RESOLUCION §14 | Documentado; defensa humana |
| G01 | main con fuente/Docker/migraciones/Excel/docs | inventario Git, .env excluida, PDF fuera | C | Preparado localmente |
| G02 | instrucciones maldanap-usac | verificar invitación/acceso en GitHub | README; sin constancia remota | PENDIENTE MANUAL |
| G03 | URL/main/carné/SHA/tag documentados | push/tag/entrega por el usuario | README/C | PENDIENTE MANUAL |
| G04 | disponibilidad durante calificación | mantenimiento remoto humano | README | PENDIENTE MANUAL |
| DOC01 | README reproducible con metadatos conocidos | clon limpio/flujo final | C/README | Técnico completo; nombre completo pendiente |
| DOC02 | RESOLUCION con diez apartados y extensiones | DER/diccionario/mapeo/ingenierías/matriz/evidencia | RESOLUCION/C | COMPLETO |

## P01–P12 individuales

Prefijos test_ de OfficialWebAcceptanceTests en tests/test_web_acceptance.py;
P06–P08 de tests/test_import_acceptance.py. P12 es operativo, no método Django.

| ID | Implementación | Prueba identificada | Evidencia | Estado |
|---|---|---|---|---|
| P01 | LoginView/LocalAuthenticationForm | P01_login_valido_e_invalido | F/C | APROBADA |
| P02 | guarda/LogoutView/inactivos | P02_sin_sesion_logout_cookie_anterior_e_inactivo | F/C | APROBADA |
| P03 | functional_access(write=True) | P03_consulta_lee_y_no_escribe | F/C | APROBADA |
| P04 | ModelForms jerarquía/Usuario | P04_jerarquia_completa_y_usuario_por_http | F/C | APROBADA |
| P05 | forms/dominio/FK/UNIQUE | P05_duplicado_y_referencia_inexistente_rechazados | F/C | APROBADA |
| P06 | importador original | P06_importar_original | I/C | APROBADA, regresión |
| P07 | reconciliación/trazabilidad | P07_repetir_importacion | I/C | APROBADA, regresión |
| P08 | políticas SE.12/NULL | P08_se12_y_ausencias | I/C | APROBADA, regresión |
| P09 | N2.clean/CHECK/form | P09_crear_y_editar_umbrales_invalidos | F/C | APROBADA |
| P10 | filtros/lista/paginación | P10_busqueda_filtros_combinaciones_y_paginacion | F/C | APROBADA |
| P11 | N2 responsable/sección | P11_responsable_otra_seccion_rechazado | F/C | APROBADA |
| P12 | persistencia Compose/volumen | scripts/verify-persistence.sh y persistence_record.py | C; dirigido 0, final por registrar | APROBADA dirigida |

## Tareas y cierre

T01/T02 contexto/diseño; T03/T05/T06 base/modelos; T07–T10 importación;
T11–T15 autenticación/funcionalidad/demo: completas, conservadas sin refactor.
T04/T16–T21 Docker/harness/P12/ciclo/documentos/ensayo: implementadas,
aceptación final registrada en C tras ejecutar. T20 cubre cinco temas/dos mejoras
reales, V1/V2/V3. T22 publicación/acceso/etiqueta/entrega: pendiente humana,
sin acciones remotas ejecutadas. No convertir metadatos desconocidos en evidencia.

## Avance CMDB (2026-10-29)

Modelo de seis entidades y migración preparados en fase V5; detalle en [MODELO](MODELO.md), [ANALISIS_CMDB](ANALISIS_CMDB.md) y [FASE_CMDB](evidencias/FASE_CMDB.md). No equivale a aprobación SD-P03/04/14/18. Matriz SD principal en [PRUEBAS](PRUEBAS.md).

| Requisito SD | Implementación de esta fase | Prueba futura / límite |
|---|---|---|
| SD-R24 | ClasificacionCI, diagrama/diccionario y mínimos observados | SD-P04; taxonomía adicional sin fuente, pendiente |
| SD-R25/26 | CI/UbicacionCI/esquema JSON/procedencia | SD-X06/SD-P03; sin importador ni generador |
| SD-R27 | ServicioCI y FK Usuario | SD-P14; sin TicketCI |
| SD-R29/34 | Modelo técnico tipado y guardas contra ciclos | SD-P04/14; sin recorrido público |
| SD-R31 | V5 y prompt SD-PE02 | Contexto real; no ciclo funcional ejecutado |

## Avance Service Desk (2026-10-29, V6)

Implementación en `src/service_desk` y `src/processes`; detalle en
[MODELO](MODELO.md#service-desk-implementado-v6), [PROCESOS](PROCESOS.md#implementación-vigente-v6)
y [FASE_SERVICE_DESK](evidencias/FASE_SERVICE_DESK.md). **Ninguna prueba SD
ejecutada**: el estado es «implementado, sin verificar».

| Requisito SD | Implementación | Prueba futura / límite |
|---|---|---|
| SD-R01 | CONSULTA recortada a lectura en `permisos.capacidades`; rol OPERATIVO sin escritura PP2 | SD-P06; regresiones PP2 por valor nuevo de rol |
| SD-R03 | `Ticket` (N1 derivado, número/UUID, fechas, canal, prioridad…) | SD-P05 |
| SD-R04 | `servicios`: crear, tomar, asignar, liberar, transferir, `ejecutar_accion`, reabrir/cerrar por definición | SD-P07/09/10 |
| SD-R05 | `TicketCI` + `motivo_sin_ci`; `RelacionTicket` tipada | SD-P05/11/13 |
| SD-R06 | `ComentarioTicket`/`AdjuntoTicket` con visibilidad; `validar_archivo`; vista `sd-adjunto` autorizada | SD-P08 |
| SD-R07 | Índices y `tickets_visibles`/`tickets_en_cola`; sin UI de búsqueda/paginación | Pendiente portal/consola |
| SD-R08 | Visibilidad propia/cola; `AccionTicket` anexable | SD-P06/08 |
| SD-R09/10 | `ColaServiceDesk`, `MembresiaCola` (usuario o rol), cinco capacidades | SD-P06 |
| SD-R11 | Orden prioridad→antigüedad→PK; `tomar_ticket` con lock advisory + `select_for_update`; `TransferenciaTicket`; bajas sin huérfanos | SD-P07 (no ejecutada) |
| SD-R12 | Definición NUEVOS_SERVICIOS + crear/vincular N2 sin duplicado | SD-P09 |
| SD-R13 | Definición CAMBIOS; ejecutar exige aprobación vigente (guarda + modelo) | SD-P10 |
| SD-R14 | Definición INCIDENTES; I0–I6, afectación, duraciones, redundancia, solución | SD-P12 |
| SD-R15 | Definición EVENTOS; E0–E3; `vincular_incidente_evento` idempotente; `Notificacion` | SD-P11 |
| SD-R16 | Definición PROBLEMAS; incidentes y cambio correctivo vía `RelacionTicket` | SD-P13 |
| SD-R17 | Definición ACCESOS; autoaprobación bloqueada (guarda + `Aprobacion.clean`) | SD-P09/06 |
| SD-R18 | Definición SERVICIOS_TECNOLOGIA con confirmación del solicitante | SD-P09 |
| SD-R19 | `MAPEO_TIPO_PROCESO` y motor común con definiciones distintas | SD-P09 |
| SD-R20 | `REFERENCIA_INCIDENTES`, `sugerir_categoria_incidente` (D54) | SD-P12 |
| SD-R21 | `NivelSoporte` 0–4 y `EQUIVALENCIA_SOPORTE_0_3` | Sin escalamiento automático entre colas |
| SD-R22/23 | No implementado (portal, FAQ, consola, tablero, indicadores) | Fase futura |
| SD-R31 | V6, prompt SD-PE03 | Contexto real; sin ciclo de Loop ejecutado |
| SD-R35 | `SD_ADJUNTOS_DIR` privado | Volumen Docker para adjuntos pendiente |
| SD-R36 | Sin demo de colas/tickets | Fase futura (≥7 colas, ≥35 tickets) |

## Cierre Service Desk (2026-10-29)

Sustituye los estados «no implementado / sin verificar» de las secciones V5/V6
anteriores. Commit `f15deb0`. E = [FASE_CIERRE_SD](evidencias/FASE_CIERRE_SD.md).
Tests en `tests/test_service_desk.py` (`test_SD_Pxx_*`). Estados:
VERIFICADO (evidencia real de bloques A/B1, EXIT=0); PARCIAL; IMPLEMENTADO /
EJECUCIÓN FINAL NO COMPLETADA (la suite de 188 tests congeló el host y no
concluyó; no se registra ni PASA ni FALLA).

| Requisito | Implementación | Test existente | Evidencia disponible | Estado |
|---|---|---|---|---|
| SD-R01 | accounts, `permisos.capacidades` (CONSULTA recortada) | SD-P01, SD-P06, PP2-P01–P03 | E: login 200, anónimo 302 | PARCIAL |
| SD-R02 | catalog, imports (`import_catalog`) | SD-P02, PP2-P06–P08 | E: N1=12, N2=46, 2ª importación 0 creados | VERIFICADO |
| SD-R03 | `Ticket`, `forms`, `views.ticket_nuevo` | SD-P05 | E: 39 tickets demo persistidos | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R04 | `servicios`, `processes.motor` | SD-P09, SD-P15 | E: 18 estados distintos en demo | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R05 | `TicketCI`, `RelacionTicket` | SD-P05, SD-P13 | — | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R06 | `ComentarioTicket`, `AdjuntoTicket`, `adjuntos.py`, `descargar_adjunto` | SD-P08 | — | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R07 | `views.filtrar`/`pagina`, `ticket_lista` | SD-P16 | E: paginación/filtros CMDB HTTP 200 | PARCIAL |
| SD-R08 | `permisos`, `AccionTicket`, `historial_visible` | SD-P06, SD-P15 | — | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R09/R10 | `ColaServiceDesk`, `MembresiaCola`, `AsignacionRolSD` | SD-P06 | E: 8 colas, 13 membresías | PARCIAL (datos verificados; permisos sin resultado) |
| SD-R11 | `tomar_ticket` (lock advisory → `select_for_update`), `TransferenciaTicket` | SD-P07, SD-P08 | — | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R12–R18 | `processes.definiciones` (7 procesos), `guardas`, `Aprobacion` | SD-P09–P13 | E: ≥5 escenarios por proceso (INCIDENTES 7) | PARCIAL (datos verificados; rutas/guardas sin resultado) |
| SD-R19/R20/R21 | `MAPEO_TIPO_PROCESO`, I0–I6 (D54), `NivelSoporte` | SD-P09, SD-P12 | — | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R22 | `views.portal`, `colas`/`cola_detalle` (consola), `faq`, `ArticuloConocimiento` | SD-P06, tests FAQ | E: 5 artículos FAQ | PARCIAL |
| SD-R23 | `indicadores.py`, `views.tablero` | SD-P17 | — | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R24 | `ClasificacionCI` acíclica (mínimo Hardware/Software) | SD-P04 | Taxonomía docente sin fuente (SD-DP01) | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R25/R26 | `CI`, `UbicacionCI`, atributos por clase | SD-P03 | E: 5000 CI en 5 clasificaciones | VERIFICADO (generación); importador Excel CMDB no implementado |
| SD-R27 | `ServicioCI`, ficha CI | SD-P14 | E: 100 vínculos CI–servicio | PARCIAL |
| SD-R28 | `generate_cmdb --count 5000 --seed 2026` | SD-P03 | E: 5000/510/100; 2ª ejecución 0/0/0 | VERIFICADO |
| SD-R29 | `cmdb/grafos.py` (BFS, profundidad 6), paginación CMDB | SD-P04, SD-P14, SD-P16 | E: 8 consultas 23.7–116.2 ms, HTTP 200 | VERIFICADO (rendimiento); ciclos sin resultado |
| SD-R30/R31/R33 | docs/prompts, AGENTS, contextos V4–V6, IA | Revisión documental | IA.md, prompts SD-PE01–PE04 | Documentado |
| SD-R32 | `scripts/verify.sh`, `probe_service_desk.py` | Harness | E: bloques A/B1 EXIT=0; suite no concluida | PARCIAL |
| SD-R34 | `cmdb/grafos.py` (G2 técnico), `service_desk/grafos.py` (ITSM) | SD-P13, SD-P14, test grafo ITSM | E: grafo de impacto HTTP 200 | PARCIAL; G1/G2 pendiente de confirmación docente |
| SD-R35 | volúmenes `datos_postgres` y `adjuntos` | SD-P18 (`verify-persistence.sh`) | No ejecutado | IMPLEMENTADO / EJECUCIÓN FINAL NO COMPLETADA |
| SD-R36 | `seed_service_desk` | SD-X08 | E: 8 colas, 37 escenarios, 39 tickets, 2ª ejecución 0 nuevos | VERIFICADO |
| SD-R37 | `tests/test_service_desk.py`, PRUEBAS | SD-P01–P18 | E: 188 tests descubiertos, suite no concluida | PARCIAL |
| SD-R38/R39 | README, docs, sin API de IA en runtime | Revisión documental | README, E | Documentado |
