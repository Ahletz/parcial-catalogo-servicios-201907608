# Service Desk: requisitos, brechas y arquitectura prevista

Fecha: 2026-10-29. Base inspeccionada: `9624e34` en `main`.
**Diseño documental, no implementación.** Fuentes y ambigüedades en
[FUENTES_SERVICE_DESK](FUENTES_SERVICE_DESK.md). T = nuevo enunciado; L22/L25 =
diapositivas. Secciones y páginas identifican la fuente de cada requisito.

## Comparación con el sistema actual

| Categoría | Elementos | Tratamiento previsto |
|---|---|---|
| Reutilizables | `accounts`: login local, Argon2id, sesiones, inactivos/logout; `organization`: seis niveles; `catalog`: N1/N2, referencias, umbrales, responsables, bajas/búsqueda; `imports`: procedencia e idempotencia; Docker, plantillas y harness | Conservar interfaces y reglas existentes. La inspección no vuelve a certificar su ejecución. |
| Nuevas funciones | Tickets/auditoría/adjuntos; colas/permisos; siete flujos; CMDB, generación, grafos; FAQ/portales; avisos e indicadores | Nuevos módulos dentro del monolito; contratos y pruebas antes de programar. |
| Cambios requeridos | `Usuario.rol` solo admite dos valores; `functional_access` exige administrador para escribir; desactivación no conoce tickets/colas; dominio serializa todas las escrituras y rechaza bulk; importación solo conoce el catálogo | Permisos de SD aditivos por capacidad y alcance; preservar CONSULTA como solo lectura; ampliar política de dependencias; estudiar concurrencia/carga sin bypass de reglas; importador CMDB separado. |
| Entregables nuevos | Modelo/jerarquía/mapeo, procesos, IA, pruebas; 8 prompts, 3 actualizaciones y 3 ciclos; al menos 7 colas, 35 tickets y 5,000 dispositivos; P01–P18 | Estado futuro explícito. No renombrar pruebas del parcial ni presentar evidencias antiguas como ejecución nueva. |

Base real: modelos en `src/accounts`, `organization`, `catalog`, `imports`;
guardas en `src/config/domain.py`; mantenimientos genéricos en
`src/config/web.py`; roles de dos valores con CHECK en `accounts/models.py`.
No existen modelos de Ticket, Cola, CI ni motor de procesos. Se encontraron
165 métodos de prueba del parcial y un escenario operativo de persistencia;
no se ejecutaron durante esta fase. La evidencia de cierre conserva pendientes
documentales de ejecución final: revisar antes de afirmar certificación global.

## Requisitos detectados

Cada SD-R es una etiqueta local de trazabilidad; no sustituye P01–P18.
La matriz requisito→módulo→implementación→prueba está en [PRUEBAS](PRUEBAS.md).

| ID | Obligación detectada | Fuente |
|---|---|---|
| SD-R01 | Conservar auth local/hash, sesiones, inactivos, bajas, autorización, jerarquía y CONSULTA de solo lectura | T §3 p.2; PP2 |
| SD-R02 | Conservar catálogo completo, responsables, validaciones, importación 12/46, SE.12, combinadas, desconocidos y códigos | T §3 p.2 |
| SD-R03 | Ticket: ID único, título, descripción, solicitante, creador, N2/N1 derivado, tipo, proceso, cola, responsable, estado, prioridad, impacto, urgencia, canal, fechas y bitácora | T §4 p.2 |
| SD-R04 | Crear, clasificar, asignar, atender, transferir, escalar, resolver, cerrar y reabrir de forma controlada | T §4 p.2 |
| SD-R05 | Ticket–CI de cero a muchos con justificación de ausencia y relaciones entre tickets | T §4 p.2 |
| SD-R06 | Comentarios públicos/notas internas, evidencias/adjuntos con tamaño, tipo y descarga autorizada | T §4 p.2 |
| SD-R07 | Búsqueda/filtros/paginación por número, servicio, proceso, cola, estado, prioridad, agente y fechas | T §4 p.2 |
| SD-R08 | Solicitante ve propios; agente colas autorizadas; administrador configura; auditoría actor/fecha/antes/después sin borrado silencioso | T §4 p.2 |
| SD-R09 | CRUD lógico de cola; un proceso exacto, código único, nombre, descripción, estado, responsables, soporte, orden y objetivos configurables | T §5 p.3 |
| SD-R10 | Asignación de colas a roles/usuarios, capacidades consultar/atender/transferir/aprobar/administrar; CONSULTA no se eleva por membresía | T §5 p.3 |
| SD-R11 | Política de asignación documentada, tomar/asignar agente autorizado, orden determinista, reclamo concurrente único, transferencias con motivo y bajas sin huérfanos | T §5 p.3 |
| SD-R12 | Nuevos servicios: necesidad/viabilidad, aprobación/rechazo, implementación y catálogo sin duplicados | T §6 p.3 |
| SD-R13 | Cambios: impacto/riesgo, autorización previa a ejecución, planificación, CI, pruebas, reversión, validación/cierre | T §6 p.3 |
| SD-R14 | Incidentes: diagnóstico/atención/escalamiento/recuperación/resolución/cierre, interrupción/degradación, I0–I6 y solución | T §6 p.3 |
| SD-R15 | Eventos: E0–E3, evaluación/respuesta, incidente idempotente y aviso verificable para E2/E3 | T §§6–7 pp.3–4 |
| SD-R16 | Problemas: incidentes, causa raíz, solución temporal, error conocido cuando aplique, definitiva y vínculo al cambio | T §6 p.3 |
| SD-R17 | Accesos: beneficiario/recurso/permiso, aprobación ajena al solicitante, provisión/revocación, validación y cierre | T §6 p.4 |
| SD-R18 | Servicios de tecnología existentes: validar, asignar, cumplir, confirmar y cerrar; distinto de incidente/nuevo servicio | T §6 p.4 |
| SD-R19 | Seis tipos docentes y mapeo explícito a siete procesos; flujos con estados/transiciones/entrada/salida/permisos propios | T §§6–7 pp.3–4; L25-14 |
| SD-R20 | Duración estimada/real, prioridad y redundancia; conservar tabla visual I0–I6 y probar regla complementaria; tiempos no son SLA | T §7 pp.4–5; L25-16 |
| SD-R21 | Soporte configurable y equivalencias 0–4/0–3, ruta de escalamiento; porcentajes solo referencia | T §7 p.5; L25-11/12/13 |
| SD-R22 | Portal solicitante, FAQ/conocimiento nivel 0, consola agente y tablero | T §7 p.5 |
| SD-R23 | Indicadores por cola/proceso/prioridad/estado, antigüedad, primera atención, resolución, cumplimiento; reglas de abiertos/pausas/reapertura/calendario | T §7 p.5 |
| SD-R24 | Transcribir y reproducir clasificación original con diagrama/diccionario y celdas/diapositivas, explicando discrepancias | T §2 pp.1–2 y §8; bloqueado por taxonomía no enumerada |
| SD-R25 | CMDB: CRUD lógico de clasificación/dispositivos/relaciones; atributos/listas originales, campos nuevos distinguidos | T §8 p.5; CM B4:U6; L22-11 |
| SD-R26 | Dispositivo: ID/código único, nombre, clasificación, estado, ubicación, responsable, técnicos por clase; IP condicional | T §8 p.5 |
| SD-R27 | Vincular CI–servicio–ticket; ficha con clasificación completa, atributos, relaciones, servicios e historial | T §8 p.5 |
| SD-R28 | Generador con semilla, al menos 5,000 dispositivos distintos persistidos, referencias existentes, distribución por nivel/categoría, datos sintéticos y repetición idempotente | T §8 pp.5–6 |
| SD-R29 | Búsqueda/filtros paginados con 5,000, relaciones navegables, clasificación acíclica, ciclos técnicos por tipo y recorrido de servicios potencialmente afectados | T §8 p.6 |
| SD-R30 | Ocho prompts usados (requisitos, CMDB, modelo, colas, procesos, seguridad, grafos, pruebas), dos mejoras comprobadas y metadatos | T §9 p.6 |
| SD-R31 | AGENTS/glosario/fuentes/modelo/reglas/decisiones/comandos, tres actualizaciones justificadas con commits, contexto por fase y confianza | T §9 p.6 |
| SD-R32 | Harness automatiza preparar/migrar/importar/generar/probar/validar, con resultados/códigos, aislamiento y límites/secretos | T §9 p.6 |
| SD-R33 | Tres ciclos reales con criterio de salida, límite e intervención; uno funcional y otro de datos/permisos; declarar fallos deliberados | T §9 p.6 |
| SD-R34 | Graph Engineering y explicación de ambos grafos; especificación del segundo grafo por aclarar | T §1 p.1 y §14 p.9; solicitud del usuario |
| SD-R35 | Compose construible, BD persistente/migraciones, comandos en contenedores, archivos Docker/env sin secretos, sesiones/adjuntos seguros, transacciones | T §10 pp.6–7 |
| SD-R36 | Demo: ≥7 colas, roles admin/solicitante/agente/aprobador y consulta, ≥35 tickets (5/proceso), distintos estados, E0–E3 e I0–I6 | T §11 p.7 |
| SD-R37 | Automatizar SD-P01–SD-P18 más regresiones PP2; comando/entrada/esperado/obtenido/fecha/commit, sin destruir evaluación | T §11 pp.7–8 |
| SD-R38 | Fuente/migraciones/Docker/originales/importadores/generador/pruebas y README/RESOLUCION/MODELO/PROCESOS/IA/PRUEBAS localizables | T §12 p.8 |
| SD-R39 | Trabajo/defensa individual, sin suscripción IA/claves en runtime, explicar decisiones/grafos y modificar código relacionado | T §§1/14 pp.1/9 |

## Módulos y estructura propuesta

Monolito Django/PostgreSQL existente. Esto es una propuesta de organización, no
directorios creados ni tecnología nueva aprobada como obligación docente.

```text
src/
  accounts/        # conservar identidad; ampliar capacidades SD y ámbitos
  organization/    # conservar jerarquía; extender guardas de baja
  catalog/         # conservar catálogo; vinculación con CI/tickets
  imports/         # conservar catálogo; añadir lector/mapeo CMDB separado
  service_desk/    # nuevo: Ticket, Cola, membresías, políticas, bitácora,
                   # comentarios, adjuntos privados y notificaciones internas
    services/      # reclamo, transferencia, cierre, reapertura y autorización
  processes/       # nuevo: 7 flujos, transiciones, aprobaciones y datos propios
  cmdb/            # nuevo: clasificación, CI, relaciones, procedencia,
                   # generación determinista y recorridos de dependencias
  knowledge/       # nuevo: FAQ/artículos y visibilidad del nivel 0
  reporting/       # nuevo: métricas calculadas desde hechos/historial
  config/          # conservar settings/rutas/dominio; integrar módulos
tests/             # añadir suites SD por dominio, permisos, concurrencia, carga
scripts/           # ampliar harness aislado y persistencia SD, en fase futura
docs/              # modelo, procesos, IA, pruebas, V4 y fuentes versionadas
```

Evitar acoplar todos los flujos a `config/web.py` o heredar CRUD genérico para
transiciones críticas. Proponer servicios de aplicación transaccionales y datos
específicos por proceso. La política de permisos se calcula en servidor sobre
usuario, capacidad, cola, ticket y estado; nunca solo por visibilidad del menú.

## Entregables y secuencia futura

Esta fase entrega los documentos enlazados, AGENTS V4 y registro de decisiones.
MODELO/PROCESOS/IA/PRUEBAS son contratos propuestos; no afirman tablas, pruebas o
ciclos ya implementados. README/RESOLUCION mantienen instrucciones/resultados PP2
con una nota de alcance, sin cambiar comandos existentes por comandos ficticios.

Secuencia recomendada tras autorizar implementación: aclarar fuentes/jerarquía y
decisiones bloqueantes → modelo/permisos → CMDB/importación/generador → tickets,
colas y concurrencia → siete flujos → portales/FAQ/adjuntos/avisos → grafos e
indicadores → demo/harness SD/pruebas dirigidas → cierre y persistencia global.
Registrar contexto/prompts/ciclos durante cada fase, no reconstruir evidencias
retroactivamente. La orden actual no autoriza ejecutar esa secuencia.

## Decisiones pendientes

| ID | Pendiente | Propuesta o condición de cierre |
|---|---|---|
| SD-DP01 | Taxonomía CMDB, niveles/rótulos/aristas originales | Solicitar aclaración o fuente que enumere la clasificación. No implementar categorías definitivas ni afirmar SD-P04 satisfecho hasta resolverla. |
| SD-DP02 | Identidad del segundo grafo de la defensa | Proponer clasificación y dependencias CI–servicio; confirmar alcance y documentar alternativas. Flujos seguirán diagramados. |
| SD-DP03 | Rol global único y roles SD múltiples | Conservar administrador/consulta PP2; añadir perfiles/capacidades SD por membresías. CONSULTA prevalece como bloqueo de toda escritura SD. Resolver migración y precedencias antes de programar. |
| SD-DP04 | Ticket de nuevo servicio exige N2 antes de crearlo | Proponer vincular al servicio existente que atiende la solicitud y guardar aparte el servicio solicitado/creado. No crear un N2 ficticio ni hacer opcional la FK sin decisión explícita. |
| SD-DP05 | Incidentes: solapamientos y hueco semana–mes | Proponer categoría elegida por agente con motivo y duración, sin clasificador automático; tabla docente conservada y casos de frontera probados. |
| SD-DP06 | Soporte y escalamiento | Proponer esquema canónico L25-11 (0–4) y equivalencias L25-12/13; configurable sin forzar porcentajes. |
| SD-DP07 | Adjuntos, cierre/reapertura, objetivos y pausas | Propuestas concretas en PROCESOS; fijar límites/formatos, actores, calendario, pausas y versionado de objetivos antes de implementación. |
| SD-DP08 | Contar dispositivos frente a CI de software | Identificar clases de dispositivos físicos y marcarlas; no contar aplicaciones, categorías ni relaciones para alcanzar 5,000. Depende de SD-DP01. |
| SD-DP09 | Carga/concurrencia y guardas existentes | Mantener integridad; evaluar coste del lock global/full_clean por registro. No permitir bulk indiscriminado; diseñar ruta validada si fuera necesaria y medir luego. |
| SD-DP10 | Transferencia entre procesos diferentes | Proponer solo cola del mismo proceso; reclasificación entre procesos como operación separada con autorización, datos de destino y bitácora íntegra. |
| SD-DP11 | PDF del parcial ausente | Usar ENUNCIADO y copia textual disponibles; incorporar PDF original si se obtiene, sin convertir texto para aparentar fuente original. |
| SD-DP12 | Reutilización de evidencias IA antiguas y entrega | Referenciar V2/V3/ciclos PP2 con alcance histórico; no asumir que cumplen todos los mínimos nuevos. Confirmar criterio docente, turno y commit evaluado; no publicar ni etiquetar en esta fase. |

No hace falta resolver todos los pendientes para terminar esta fase documental.
SD-DP01 bloquea concretar la clasificación; los demás acotan decisiones que deben
cerrarse antes de implementar su componente. No se omiten requisitos por falta
de una fuente: se marcan como pendientes verificables.
