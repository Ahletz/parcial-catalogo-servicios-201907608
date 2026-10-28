# Matriz y plan de verificación de Service Desk

Fecha: 2026-10-29. Base inspeccionada `9624e34`.
**Todas las pruebas SD son futuras: NO IMPLEMENTADAS / NO EJECUTADAS.**
No se ejecutó ninguna suite durante la actualización del contexto.
Fuente: T §11 pp.7–8, [inventario](FUENTES_SERVICE_DESK.md).

`PP2-P01`–`PP2-P12` designa los escenarios antiguos, cuyos métodos no se renombran.
`SD-P01`–`SD-P18` designa los nuevos: SD-P02 no es el logout del parcial,
SD-P12 no es su persistencia y SD-P18 amplía la persistencia a todo Service Desk.
La [matriz anterior](MATRIZ_TRAZABILIDAD.md) conserva resultados históricos.

## Requisito → módulo → implementación prevista → prueba futura

IDs SD-R definidos en [SERVICE_DESK](SERVICE_DESK.md). Los nombres de módulos
nuevos son propuesta; ninguna referencia a ellos acredita implementación.

| Requisito | Módulo | Implementación prevista | Prueba futura |
|---|---|---|---|
| SD-R01 | accounts, organization, service_desk | Mantener auth/hash/sesiones/bajas; añadir capacidades sin elevar CONSULTA | SD-P01/P06 y regresiones PP2 |
| SD-R02 | catalog, imports | Conservar importador y todos los datos/reglas originales | SD-P02; PP2-P06/P07/P08/P09/P11 |
| SD-R03 | service_desk | Modelo/formulario Ticket explícito, FK válidas, N1 derivado | SD-P05 |
| SD-R04 | service_desk, processes | Servicios de transición, resolución/cierre/reapertura | SD-P09/P15 |
| SD-R05 | service_desk, cmdb | TicketCI y RelacionTicket; ausencia CI motivada | SD-P05/P13/P14; SD-X01 |
| SD-R06 | service_desk | Visibilidad de comentarios y archivos privados con validaciones | SD-X02 |
| SD-R07 | service_desk | Consulta autorizada, filtros y paginación estable | SD-X03 |
| SD-R08 | service_desk, accounts | Ámbitos propios/cola/admin y bitácora inmutable | SD-P01/P06/P15; SD-X02 |
| SD-R09 | service_desk, processes | Cola con proceso único, soporte, orden y objetivos | SD-P06/P08/P09; SD-X04 |
| SD-R10 | accounts, service_desk | Membresía usuario/rol y permisos separados | SD-P01/P06/P10 |
| SD-R11 | service_desk | Reclamo atómico, desempate, traslado auditado y bajas bloqueadas | SD-P07/P08; SD-X04 |
| SD-R12 | processes, catalog | Flujo nuevos servicios y creación/vínculo sin duplicar N2 | SD-P09/nuevos_servicios |
| SD-R13 | processes, cmdb | Cambio aprobado, planes, CI, ejecución/validación/reversión | SD-P09/cambios; SD-P10 |
| SD-R14 | processes | Incidente con recuperación, solución y escalamiento | SD-P09/incidentes; SD-P12 |
| SD-R15 | processes, service_desk | Evento idempotente e incidente/aviso persistentes | SD-P09/eventos; SD-P11 |
| SD-R16 | processes | Problema con causa/soluciones/error y vínculos | SD-P09/problemas; SD-P13 |
| SD-R17 | processes, accounts | Acceso aprobado por otra identidad y validación de resultado | SD-P09/accesos; SD-P10 |
| SD-R18 | processes | Solicitud existente con cumplimiento/confirmación | SD-P09/servicios_tecnologia |
| SD-R19 | processes | Tabla tipo→proceso y siete guardas distintas | SD-P09 y revisión PROCESOS |
| SD-R20 | processes | Tabla docente y selección complementaria motivada | SD-P12 |
| SD-R21 | processes, service_desk | Soporte configurable, equivalencias y ruta escalada | SD-P09/incidentes; SD-X05 |
| SD-R22 | knowledge, service_desk | FAQ/portal propio/consola y tablero autorizado | SD-X05; SD-P06/P17 |
| SD-R23 | reporting | Cálculos desde hechos, objetivos versionados, reloj/pausas/ciclos | SD-P17 |
| SD-R24 | cmdb, docs | Taxonomía trazada a origen y árbol acíclico | SD-P04; bloqueado SD-DP01 |
| SD-R25 | cmdb, imports | Mantenimiento/lector CMDB con mapeo de todos los campos | SD-P04/P05; SD-X06 |
| SD-R26 | cmdb | Campos operativos/atributos por clase y restricciones | SD-P03/P05; SD-X06 |
| SD-R27 | cmdb, catalog, service_desk | Ficha de CI, relaciones y servicios/tickets asociados | SD-P13/P14 |
| SD-R28 | cmdb | Generador de conjunto/semilla, códigos estables y reporte por nivel | SD-P03 |
| SD-R29 | cmdb | Paginación/vecindarios, validación de ciclos y recorrido inverso | SD-P04/P14/P16 |
| SD-R30 | docs/prompts, IA | Ocho prompts reales + dos mejoras con evidencias/commits | SD-X07 documental |
| SD-R31 | AGENTS, docs/contexto | Actualizaciones motivadas, glosario y selección por fase | SD-X07 documental |
| SD-R32 | scripts, Docker, tests | Harness ampliado con aislamiento/códigos y verificación | SD-X07; SD-P18 |
| SD-R33 | docs/evidencias | Tres ciclos observados, límites y correcciones reales | SD-X07 documental |
| SD-R34 | cmdb, docs | G1/G2 propuestos y explicación de recorridos/limitaciones | SD-P04/P14; SD-X07; pendiente SD-DP02 |
| SD-R35 | config, Docker, scripts | Persistencia DB/adjuntos, migraciones y sesiones protegidas | SD-P01/P18; SD-X02 |
| SD-R36 | comandos demo futuros | Dataset controlado: ≥7 colas, ≥35 tickets, roles y casos E/I | SD-X08; SD-P09/P11/P12 |
| SD-R37 | tests, docs/PRUEBAS | Escenarios aislados y registro de resultados/commit | SD-P01–SD-P18 y SD-X01–SD-X08 |
| SD-R38 | README, docs, Git | Entregables localizables y fuentes intactas | SD-X07 documental |
| SD-R39 | runtime, docs, defensa | Sin API IA obligatoria; comprensión y modificación humana | SD-X07, SD-P18 y defensa individual |

## Los dieciocho escenarios obligatorios

Los identificadores `test_Pxx` son nombres propuestos para una suite futura,
no funciones existentes. La tabla registra entrada y resultado esperado; el
resultado obtenido es **pendiente** en los 18 casos.

| ID | Entrada / acción | Resultado esperado | Nivel y módulo previsto |
|---|---|---|---|
| SD-P01 | Login válido/incorrecto, logout/cookie previa, inactivo y acciones con perfil sin capacidad | Auth local correcta; sesiones inválidas rechazadas; ninguna escritura por CONSULTA | Integración HTTP/accounts/service_desk |
| SD-P02 | Original catálogo, segunda/tercera importación y ediciones humanas | 12/46 importados, sin duplicados; incidencias SE.12/42/67 y desconocidos/códigos conservados; divergencias protegidas | Integración/imports + regresiones |
| SD-P03 | Referencias válidas y generador con semilla S, ≥5,000; repetir S | ≥5,000 dispositivos únicos persistidos, no filas auxiliares/software; repetir no duplica, reporte por nivel/categoría coherente | Integración/carga cmdb; SD-DP01/08 previos |
| SD-P04 | Taxonomía confirmada vs celdas/diapositivas; padre inexistente, autopadre y ciclo indirecto | Correspondencia trazable; referencias y ciclos inválidos rechazados; árbol válido recuperable | Unitario+integración/cmdb; bloqueado SD-DP01 |
| SD-P05 | Alta ticket completo, N2/usuario/cola/proceso/CI válidos; después IDs inexistentes y combinación incoherente | Guarda válido; rechaza referencias/campos inválidos; N1 derivado, no sobreescribible | Integración HTTP/service_desk |
| SD-P06 | Cola para rol, para usuario, para ambos; agente ajeno; CONSULTA miembro | Capacidades/ámbitos respetados en lectura y cada escritura; membresía no eleva consulta | Integración/permisos |
| SD-P07 | Tickets con prioridades/fechas empatadas y dos conexiones reclamando el mismo | Orden prioridad/edad/PK reproducible; exactamente un agente gana; otro recibe conflicto y bitácora consistente | Concurrencia real PostgreSQL/service_desk |
| SD-P08 | Transferir a cola válida/otra de proceso incompatible, sin permiso, inactiva | Solo destino/política válidos; motivo, cola/responsable anterior/nuevo y actor conservados; sin huérfanos | Integración/concurrencia/service_desk |
| SD-P09 | Siete casos independientes recorren la ruta completa; intentar saltos inválidos | Cada proceso valida sus datos/actores/entrada/salida; siete rutas completas y rechazos observables | Integración HTTP/processes |
| SD-P10 | Ejecutar cambio sin aprobación; solicitante intenta aprobar su acceso, incluso con rol admin/aprobador | Ambas operaciones rechazadas en servidor y sin efecto parcial | Integración/seguridad/processes |
| SD-P11 | E0/E1/E2/E3, reintentar procesamiento E2/E3 y vincular incidente existente | E0 registro; E1 evaluación sin respuesta; E2/E3 incidente+aviso visible, sin duplicados | Integración/idempotencia/processes |
| SD-P12 | I0–I6, duraciones desconocidas, solapadas y hueco semana–mes; prioridades/redundancias | Tabla docente conservada; regla complementaria/motivos aplicada; nulo distinto de cero, sin SLA inventado | Unitario+integración/processes |
| SD-P13 | Incidente→problema→cambio y consulta de enlaces desde cada expediente | Cadena recuperable, actor/fechas/evidencias; no perder historial al cerrar | Integración/processes |
| SD-P14 | CI dependiente/proveedor→servicio, ciclo técnico permitido y prohibido | Recorrido correcto con camino y permisos; clasificación sin ciclos; bucles admitidos terminan; impacto solo potencial | Unitario+integración/cmdb |
| SD-P15 | Cerrar sin resolución/resultado, cerrar válido y reabrir con/sin permiso/motivo | Rechaza cierre inválido; cierre y reapertura controlados; conserva actor, antes/después, ciclos e historia | Integración/service_desk/processes |
| SD-P16 | 5,000 dispositivos; filtros por código/nombre/clase/estado/ubicación/responsable y varias páginas | Resultados exactos, sin saltos/duplicados; registrar latencias observadas, tamaño de página y entorno real | Integración+medición/cmdb |
| SD-P17 | Reloj fijo, tickets cerrados/abiertos, sin atención, pausas abiertas/solapadas, reaperturas | Indicadores coinciden con cálculo manual; abiertos no aparecen como resueltos/cumplidos; nulos/denominador cero explícitos | Unitario+integración/reporting |
| SD-P18 | Dataset catálogo+CMDB+35 tickets+historia+adjuntos; reiniciar/recrear sin borrar volumen | IDs/conteos/contenido/campos e historial persistentes; adjuntos descargables solo con permiso | Operativo Docker con proyecto aislado |

## Comprobaciones adicionales necesarias

| ID | Cobertura que no debe perderse entre P01–P18 |
|---|---|
| SD-X01 | Ticket sin CI con/sin justificación; relaciones entre tickets válidas y sin autosreferencias indebidas. |
| SD-X02 | Notas internas ocultas en lista/detalle/descarga al solicitante; CSRF; acceso directo a adjunto ajeno; límites MIME/tamaño/nombre y contenido malicioso rechazados. |
| SD-X03 | Todos los filtros de tickets, combinaciones, fechas límite, números inexistentes y paginación estable bajo ámbito autorizado. |
| SD-X04 | CRUD/bajas de colas, usuarios y roles con tickets pendientes; no huérfanos; conservar historia tras reasignación explícita. |
| SD-X05 | FAQ/nivel 0, portal propio y consola; escalamiento/soporte equivalentes sin cuotas porcentuales forzadas. |
| SD-X06 | CMDB: 20 columnas mapeadas, blancos/espacios/fechas/encoding, referencias sin resolver, atributos por clase e IP opcional, originales inmutables. |
| SD-X07 | Auditoría documental: mínimos IA, fuentes/hashes, commits/resultados verdaderos, Docker/README reproducibles, sin secretos ni dependencia de proveedor IA. |
| SD-X08 | Demo repetible: ≥7 colas funcionales (1/proceso), ≥35 tickets (5/proceso), varios estados, E0–E3/I0–I6, roles requeridos y consulta sin escritura. |

## Rutina futura y registro de resultados

No ejecutar en esta fase. Primero implementar los módulos y pruebas; después
documentar comandos exactos en contenedores para preparación, migración,
importación del catálogo, importación/generación CMDB, demo, pruebas dirigidas,
validación de integridad/grafos y persistencia. Los comandos nuevos aún no existen.
No añadir `generate_cmdb` al README como si fuera un comando disponible.

Para cada ejecución real registrar: ID, comando exacto, parámetros/semilla,
entrada controlada, resultado esperado, resultado obtenido, código de salida,
fecha/zona horaria, SHA probado, entorno/versiones y ruta de evidencia. En
mediciones: hardware/recursos, volumen de datos, filtros/índices relevantes,
repeticiones y latencias observadas; T no fija un umbral de rendimiento universal.

Aislar bases `test_`/proyectos/volúmenes y adjuntos sintéticos; nunca modificar
evaluación. Pruebas de concurrencia usarán transacciones/conexiones distintas,
no llamadas secuenciales disfrazadas. Conservar regresiones PP2 dirigidas al
área afectada. Suite completa y Docker global solo cuando una fase futura lo
autorice; `scripts/verify.sh` actual incluye una suite completa y no se ejecuta
para revisar documentación.

## Validación de esta fase documental

Únicamente inspección de fuentes/código/historial, enlaces locales, cobertura de
IDs, coherencia del alcance y `git diff --check`. No equivale a aprobar SD-P01–P18.
Resultados de esos controles se registran en CONTEXTO_V4 y en el resumen de fase;
las evidencias históricas no se modifican para aparentar ejecuciones nuevas.

## Estado parcial V5 — modelo CMDB

ClasificacionCI/UbicacionCI/CI/TipoRelacionCI/RelacionCI/ServicioCI y migración preparados. Check y revisión de migraciones son controles ligeros, no SD-P04 ni pruebas de ciclos. Resultados reales y limitación PostgreSQL/original en [FASE_CMDB](evidencias/FASE_CMDB.md). La taxonomía adicional sigue sin fuente.
