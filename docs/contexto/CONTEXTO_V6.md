# CONTEXTO V6 — CMDB integrada y núcleo Service Desk implementado

Fecha: 2026-10-29, America/Guatemala. Anterior [V5](CONTEXTO_V5.md).
Herramienta: Claude Code (VS Code), modelo Claude Opus 5.5. Base 35403e6
(CMDB integrada por fast-forward). Prompt [SD-PE03](../prompts/SD_P03_SERVICE_DESK.md).

## Hallazgos reales → cambio de contexto

| Antes (V5) | Hallazgo y fuente | Después (V6) |
|---|---|---|
| CMDB preparada en copia; «no afirmar aplicación al original» | Bundle aplicado con `merge --ff-only`; migración `cmdb.0001` aplicada en PostgreSQL 17 efímero ([evidencia](../evidencias/FASE_SERVICE_DESK.md)) | CMDB integrada en `main` con sus commits originales. Aplicada solo a BD efímera, no al volumen de evaluación. |
| `Usuario.rol` con dos valores; roles SD «pendientes» (SD-DP03) | CONSULTA debe bloquear toda escritura y la escritura PP2 exige ADMINISTRADOR: un agente/solicitante/aprobador no cabe en ninguno sin romper una invariante | Tercer valor global `OPERATIVO` (sin escritura PP2) + roles SD aditivos `AsignacionRolSD` y `MembresiaCola`. Migración `accounts.0002_rol_operativo`. |
| Reclamo concurrente «a estudiar» con lock global (SD-DP09) | Todo `save()` de dominio toma `pg_advisory_xact_lock`; bloquear la fila antes que el lock global puede interbloquear con otro save | Orden fijo: `domain_transaction()` (lock advisory) **y después** `select_for_update` de la fila. Toda operación de ticket pasa por `service_desk.servicios`. |
| Flujos «propuestos» en PROCESOS | Implementación exige estados finos por proceso y guardas en modelo y servicio | Motor `processes.motor` + 7 `DefinicionProceso`; aprobación con huella del contenido; detalle propio por proceso. |

Estos cambios alteran invariantes de AGENTS (roles, concurrencia, estado de
implementación); no es una versión de relleno.

## Decisiones cerradas en esta fase

D47–D56 en [DECISIONES](../DECISIONES.md): SD-DP03 (roles), SD-DP04 (N2 de
atención + resultado aparte), SD-DP05 (bandas complementarias I0–I6 solo como
sugerencia), SD-DP06 (0–4 canónico, equivalencia 0–3), SD-DP07 parcial
(adjuntos 10 MiB PDF/PNG/JPEG/TXT), SD-DP09 parcial (orden de locks) y
SD-DP10 (transferencia solo mismo proceso).

## Estado y límites

Implementado: modelos, migraciones, permisos, servicios, motor, 7 procesos,
vista protegida de descarga. Validado solo con `check`, `makemigrations
--check --dry-run` y `migrate` en BD efímera. **Sin pruebas funcionales**:
P07 concurrente, guardas de flujo, adjuntos y regresiones PP2 pendientes.
Pendientes de interfaz (portal, consola, tablero), FAQ, indicadores, demo de
≥7 colas/≥35 tickets, generador 5,000 CI, volumen Docker para adjuntos.

## Commits

Recuperar sin hash autorreferente:

~~~bash
git log -1 --diff-filter=A --format='%H %s' -- docs/contexto/CONTEXTO_V6.md
git log --oneline 35403e6..HEAD
~~~
