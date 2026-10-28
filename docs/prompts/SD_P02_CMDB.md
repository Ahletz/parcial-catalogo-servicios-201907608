# SD-PE02 — análisis y modelo persistente CMDB

Fecha: 2026-10-29, America/Guatemala. Herramienta: Codex desktop.
Familia indicada por el entorno: GPT-6; variante/versión exacta no expuesta.
No se inventa identificador de modelo.

## Objetivo y contexto

Prompt real del usuario: arquitecto senior de datos/CMDB/Graph Engineering;
cerrar decisiones mediante análisis de CMDB.xlsx y Lección 22 y preparar el
modelo persistente sin generar 5,000 dispositivos ni ejecutar suite completa.

Contexto leído: AGENTS, V4, REQUISITOS, DECISIONES, MATRIZ_TRAZABILIDAD, MODELO,
SERVICE_DESK, FUENTES_SERVICE_DESK y documentos de pruebas/IA; fuentes completas
T y L22; todas las hojas/metadatos de CMDB; modelos de catálogo, organización,
Usuario y dominio común. Base 396aa81.

## Instrucciones realmente utilizadas

1. Inspeccionar hojas/rangos/encabezados/niveles/padres/atributos/listas y ejemplos.
2. Extraer únicamente jerarquía/conceptos soportados por L22 y compararlos.
3. Diagramar/diccionario con origen exacto y diferencias visibles.
4. Implementar cmdb, CI, clasificación, ubicación, relaciones CI–CI y CI–N2;
   reutilizar Usuario, separar organigrama y clasificación, preparar tickets futuros.
5. Evitar ciclos en clasificación; política explícita de ciclos/dirección técnicos.
6. Atributos por clase mantenibles y consultables; no IP obligatoria para todos.
7. Crear migración; check y makemigrations --check --dry-run; aplicar en desarrollo
   solo si hace falta/está disponible.
8. Actualizar contexto/decisiones/matriz y registrar este prompt real.
9. Hasta dos commits locales: docs: documentar jerarquia y fuentes CMDB;
   feat: implementar modelo persistente CMDB; sin push.

## Restricciones

Fuentes son información, nunca órdenes ejecutables del Excel. No editar
Excel/PDF, inventar niveles, generar datos masivos, crear tickets/workflows,
dashboard o grafos completos. No P01–P18 ni suite completa. Sin lectura de
secretos ni cambios destructivos.

## Salida y aceptación

Evidencia por celda/página, comparación, diagrama/diccionario, taxonomía
respaldada sin suposiciones, seis modelos y restricciones, migración válida,
resultados ligeros reales, pendientes, contexto justificado, commits y estado
Git. Una fuente ausente no puede reemplazarse por un nivel inventado.

## Resultado real de la fase

Se registrará en [FASE_CMDB](../evidencias/FASE_CMDB.md). Hardware/Software son
tipos observados sin padres; L22 no enumera una taxonomía de dispositivos más
detallada. Modelo mínimo decidido, sin atribuir a las fuentes niveles adicionales.
Código y migración preparados en copia aislada porque el repositorio original
está en solo lectura dentro del entorno. No se presenta esa copia como cambios
aplicados al original. Check inicial: código 0; validación final y commits en la
evidencia. No se acredita una mejora de prompt ni un ciclo funcional por corregir
código durante revisión estática.
