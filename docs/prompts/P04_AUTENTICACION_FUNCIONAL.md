# PROMPT-04 — AUTENTICACIÓN y funcionalidad web

Fecha: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo/versión exacta disponible: PENDIENTE DE REGISTRAR MANUALMENTE.
Solicitud real del usuario, recibida como texto adjunto; extracto seleccionado.
Cuarto tema obligatorio: AUTENTICACIÓN; integra funcionalidad pendiente.

## Objetivo y contexto suministrado

Completar en una fase login/logout, roles, organización/usuarios, catálogo,
responsables, UI mínima, demo y P01–P05/P09–P11. Fecha de entrega inminente:
priorizar obligatorios, pruebas y funcionalidad antes de mejoras visuales.
Leer AGENTS, ENUNCIADO, V3, decisiones, modelo, matriz y evidencias de modelo e
importación. Inspeccionar implementación/Git. Reutilizar Django 5.2/PostgreSQL 17,
usuario personalizado, modelos, importador y las 126 pruebas aprobadas.
Los documentos delimitan alcance, reglas efectivas y controles ya verificados.

## Instrucciones usadas

~~~text
Implementa autenticación local Django con el identificador aprobado y Argon2id.
Logout invalida sesión; inactivos no entran ni usan una sesión previa.
ADMINISTRADOR mantiene; CONSULTA lee y toda escritura se rechaza en servidor.
Construye listar/crear/editar/desactivar para organización, usuarios, N1/N2
y clasificaciones con plantillas reutilizables. Respetar jerarquía y bajas.
N2: código/nombre, N1/estado/clase/criticidad/tipo, paginación y ficha completa.
Validar umbrales, referencias y pertenencia del responsable en servidor.
Mantener importados sin asignación y valores desconocidos, NULL distinto de cero.
seed_demo idempotente: dos roles, jerarquía y tres asignaciones válidas;
credenciales desde variables de entorno documentadas, sin secretos reales en Git.
Crear pruebas explícitas P01–P05/P09–P11. P06–P08 son regresiones aprobadas;
P12 queda pendiente. Pruebas dirigidas durante desarrollo; suite completa al final.
Registrar cambios, comandos, resultados reales, errores y correcciones.
~~~

## Restricciones

No rehacer modelos/importador/trace; no modificar Excel/enunciado; no leer ni
mostrar secretos. No SPA/framework frontend/API innecesaria, OAuth/MFA,
microservicios ni funcionalidades fuera del parcial. No inventar evidencias,
segunda mejora ni V4. No push/tag/reset destructivo/rebase. Máximo dos commits
locales preferidos, implementación y evidencia. No suite completa por cada cambio.

## Salida y criterio de aceptación

Reportar funcionalidades, archivos principales, configuración demo, resultados
P01–P05/P09–P11, total final, fallos/correcciones, mejora real si ocurre,
pendientes finales, commits y estado Git; evitar explicación extensa.
Termina con web funcional, roles efectivos, tres asignaciones, tests nuevos y
regresiones aprobados, suite completa satisfactoria, hashes intactos y solo P12
oficial pendiente. Resultado real y commit se registran en
[FASE_FUNCIONAL.md](../evidencias/FASE_FUNCIONAL.md), sin anticipar aprobaciones.
