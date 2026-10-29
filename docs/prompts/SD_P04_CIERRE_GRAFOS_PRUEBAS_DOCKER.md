# SD-PE04 — CIERRE / GRAFOS / PRUEBAS / DOCKER

Fecha: 2026-10-29, America/Guatemala. Herramienta: Claude Code (extensión VS
Code). Modelo indicado por el entorno: Claude Opus 5.5 (`claude-opus-5-5`).

## Objetivo

Prompt real del usuario (Tech Lead/DevOps/QA, «modo entrega acelerada»): cerrar
la tarea Service Desk en una sola fase: volumen de adjuntos, generador de 5,000
CI, datos demo (≥7 colas, ≥35 tickets), portal, consola, administración mínima,
FAQ, dos grafos, tablero, búsqueda/paginación, reclasificación, harness,
documentación, SD-P01–P18 al final, verify.sh una vez (máximo dos), commits y
push a main.

## Contexto suministrado

AGENTS V6, MODELO, PROCESOS, MATRIZ, IA, README y sección 12–14 de
Tarea_Service_Desk.pdf (entregables, rúbrica, defensa). Código de servicios,
permisos, motor, modelos, plantillas y harness existentes.

## Instrucciones y restricciones realmente aplicadas

- Orden fijo de trabajo y prioridad A (funcionalidad) > B (pruebas) > C (datos)
  > D (Docker/harness) > E (docs) > F (estética).
- Sin refactor ni dependencias nuevas; plantillas Django, CSS local, sin
  librería frontend (los grafos se dibujan como SVG desde el servidor).
- 5,000 CI generados una vez para validación; verify.sh una vez y, si falla,
  subconjunto + una segunda y última ejecución.
- No inventar ciclos, prompts, mediciones ni modelo/herramienta; no crear V7
  salvo hallazgo real; no tag no exigido; push sin force.

## Decisión de alcance tomada sin preguntar (regla 18)

Las subclases de Hardware (Servidor, Estación, Red, Almacenamiento, Impresora)
y Aplicación bajo Software son **clases del conjunto sintético** (D57), con
`datos_origen` que lo declara; Hardware/Software siguen siendo las únicas
clases con respaldo de fuente. La demo de «Nuevos servicios» vincula servicios
existentes para no alterar el conteo 12/46 del catálogo; la creación de N2 se
prueba en SD-P09.

## Resultado

Ver [FASE_CIERRE_SD](../evidencias/FASE_CIERRE_SD.md), [PRUEBAS](../PRUEBAS.md) e
[IA](../IA.md#cierre-service-desk--sd-pe04).
