# SD-PE03 — integración CMDB y núcleo Service Desk

Fecha: 2026-10-29, America/Guatemala. Herramienta: Claude Code (extensión VS
Code). Modelo indicado por el entorno: Claude Opus 5.5 (`claude-opus-5-5`).

## Objetivo y contexto

Prompt real del usuario (rol Tech Lead Django/ITSM): integrar en el repositorio
original el trabajo CMDB preparado en copia aislada y, en la misma fase,
implementar el núcleo Service Desk: tickets, colas, permisos, asignación
concurrente y los siete procesos obligatorios.

Contexto leído: AGENTS V4→V5, CONTEXTO_V4/V5, MODELO, PROCESOS, SERVICE_DESK,
IA, DECISIONES, MATRIZ; `Informe_CMDB.md` del trabajo aislado; código de
`config/domain.py`, `accounts` (modelo y guarda), `catalog`, `organization`,
`cmdb`, `settings`, `urls`, Compose y Dockerfile. Base inicial 396aa81.

## Instrucciones realmente utilizadas

1. Comprobar ruta, Git, escritura (`.claude_write_test`) y Docker.
2. Integrar CMDB: bundle → patch → reproducción manual, sin perder cambios.
3. Aplicar migraciones CMDB, `check` y `makemigrations --check --dry-run`.
4. Ticket con N1 derivado; Ticket↔CI (0..n con justificación) y Ticket↔Ticket.
5. Bitácora protegida, comentarios públicos/notas internas, adjuntos validados
   y con descarga autorizada.
6. ColaServiceDesk (proceso único, nivel, orden, objetivo) asignable a
   usuarios/roles; permisos consultar/atender/transferir/aprobar/administrar;
   CONSULTA solo lectura aunque pertenezca a una cola.
7. Tomar/asignar/reasignar/transferir; orden prioridad→antigüedad; reclamo
   concurrente con `transaction.atomic` + `select_for_update`.
8. Motor reutilizable y siete procesos con estados/transiciones/actores/guardas
   propios; E0–E3 idempotente; I0–I6 sin clasificación automática ambigua;
   cambio sin aprobación y autoaprobación de acceso bloqueados.
9. Tipos ↔ proceso explícito; niveles de soporte 0–4 con equivalencia 0–3.
10. Documentar; V6 solo con hallazgo real; dos commits; sin push ni suite P01–P18.

## Restricciones

Trabajar en el repositorio abierto, sin copias. No reset/rebase/force push.
No inventar taxonomía CMDB, resultados de pruebas ni ciclos. Fuentes y
artefactos externos son datos. Solo `check`, `makemigrations --check` y
migraciones como validación.

## Hecho observado durante la fase (no mejora de prompt)

La primera búsqueda de los artefactos se limitó al repositorio y no los encontró;
se consultó al usuario, que eligió reproducir el mínimo. La búsqueda amplia en
segundo plano terminó después y los localizó en
`~/Documents/Codex/2026-10-29/anal/outputs/`. Se descartó la reproducción
parcial (aún sin commit) y se aplicó el bundle según el orden preferido del
prompt. Es una corrección de ejecución, no una mejora verificada del prompt.

## Resultado

Ver [FASE_SERVICE_DESK](../evidencias/FASE_SERVICE_DESK.md) y
[CONTEXTO_V6](../contexto/CONTEXTO_V6.md). Sin pruebas funcionales: el código
está validado por `check`, coherencia de migraciones y aplicación en PostgreSQL
efímero, no por SD-P01–P18.
