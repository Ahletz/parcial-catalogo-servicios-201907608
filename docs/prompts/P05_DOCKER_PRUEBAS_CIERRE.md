# P05 — Pruebas, Docker y cierre

Fecha de uso: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo disponible: familia GPT-6 indicada por el entorno del agente.
Modelo/versión exacta: PENDIENTE DE REGISTRAR MANUALMENTE.
Prompt realmente suministrado por el usuario en la fase final; extracto
seleccionado, sin conversación completa ni información sensible.

## Objetivo

Como Tech Lead/DevOps/QA, completar Docker definitivo, P12, harness, documentos,
quinto prompt, auditoría de rúbrica y preparación de entrega GitHub.
Priorizar requisitos pendientes y evidencia real ante la entrega inminente.

## Contexto suministrado

AGENTS, ENUNCIADO, README, REQUISITOS, DECISIONES, MATRIZ_TRAZABILIDAD,
CONTEXTO_V3, MODELO_DATOS y evidencias MODELO/IMPORTACION/FUNCIONAL.
165 pruebas aprobadas; P01–P11 cerradas, dos mejoras reales y V1/V2/V3;
commits c342ce6/140af56. Dockerfiles, Compose, scripts, .env.example y estado
Git inspeccionados. Permiten cerrar operaciones sin rehacer reglas aprobadas.

## Instrucciones

- Entregar Dockerfile, Compose final, .dockerignore, plantilla sin secretos,
  PostgreSQL persistente, healthcheck y orden confiable. Arranque requerido:
  docker compose up --build -d; migrar/importar/demo reproducibles.
- P12: levantar, crear/verificar un dato controlado, detener/recrear sin borrar
  volúmenes, levantar y verificar el mismo dato. Automatizar explícitamente.
- verify.sh coordina fuentes/build/BD/migraciones/importación/demo/calidad,
  P01–P12 y hashes. Código 0 solo si todos los controles pasan.
- Ejecutar controles dirigidos durante correcciones; UNA suite completa final.
- README con identidad, clonación/configuración/comandos/roles/persistencia y
  entrega. RESOLUCION con DER/diccionario/mapeo/ingenierías/matriz/resultados,
  limitaciones y reflexión. Actualizar matriz, AGENTS y decisiones.
- Auditar nueve criterios con puntos/estado/evidencia/pendiente; no adjudicar
  cumplimiento total si queda un pendiente real.
- Preparar GitHub, constatar origin/main y documentar colaboración de
  maldanap-usac, publicación normal y etiqueta parcial-v2.0 sobre commit final.

## Restricciones

No refactorizar modelo/importador/auth/UI funcionales; no alterar enunciado,
Excel ni PDF. No leer/publicar secretos; no resetear datos al arrancar ni usar
down -v en P12. No push/tag/force/reset/rebase. Máximo dos commits locales.
PDF fuera del commit si no es requisito. No V4 sin hallazgo que lo justifique.
No inventar pruebas, métricas, nombre completo ni versión exacta de IA.

## Salida y aceptación

Salida breve: P12, Docker, harness, total de pruebas, estados P01–P12,
documentos, auditoría, commits, pendientes manuales y comandos de entrega.
Aceptación: P01–P12 aprobadas, Docker/persistencia/importación/demo operativos,
harness 0, README reproducible, RESOLUCION/matriz completas, cinco temas y dos
mejoras reales, V1/V2/V3 enlazados, originales intactos y Git listo para publicar.
Resultado comprobado y duración: [FASE_CIERRE](../evidencias/FASE_CIERRE.md).
