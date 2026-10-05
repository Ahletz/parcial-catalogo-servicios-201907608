# Prompt usado — base Django y modelo persistente

ID: PROMPT-02 (no equivale a la prueba funcional P02).
Fecha: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo/versión exacta: PENDIENTE DE REGISTRAR MANUALMENTE.
Contexto base: f5f39e3 y documentos enumerados en CONTEXTO_V2.

## Objetivo, contexto y aceptación

Objetivo: cerrar PD01–PD09 e implementar base, usuario, organización, catálogo,
procedencia, migraciones y pruebas internas. Contexto: AGENTS/enunciado/V1,
requisitos, análisis Excel, decisiones, matriz y Git; conservan acuerdos y
delimitan alcance antes de editar.

Extractos realmente utilizados de la solicitud actual del usuario:

~~~text
ROL: Arquitecto de software senior y desarrollador Django/PostgreSQL especializado en modelado de dominio e integridad de datos.

OBJETIVO:
Cerrar las decisiones técnicas pendientes del contexto V1 e implementar la base estructural y el modelo persistente del proyecto, incluyendo migraciones y pruebas de integridad del dominio.

No continúes con implementación hasta que PD01–PD09 queden resueltos o exista una justificación explícita para mantener alguno pendiente.

El usuario personalizado debe existir antes de generar las primeras migraciones.
No usar SQLite como base funcional del proyecto.

Las reglas importantes deben existir en servidor/dominio y, cuando sea razonable, también mediante constraints de PostgreSQL.

Crear únicamente el MODELO persistente necesario para soportar posteriormente el importador.

Estas NO sustituyen P01–P12.
Son pruebas internas iniciales del modelo.
No marques P01–P12 como completadas.

NO modificar ENUNCIADO.md.
NO modificar data/CatalogoServicios.xlsx.
NO ejecutar todavía la importación completa.
NO implementar todavía toda la interfaz.
NO implementar todavía Docker completo si no es estrictamente necesario para esta fase.
NO leer ni publicar secretos.
NO inventar resultados de pruebas.
NO modificar pruebas para esconder fallos.
~~~

Instrucciones adicionales de la misma solicitud: implementar los cinco módulos
aprobados con Python 3.13/Django 5.2/PostgreSQL 17; campos y jerarquía mínimos;
trece casos internos obligatorios; ejecutar controles, corregir/reportar fallos
y actualizar contexto solo por hallazgo real.

Salida esperada: decisiones, archivos/estructura/modelos/constraints/migraciones,
pruebas, comandos y resultados, fallos/correcciones, motivo de V2, pendientes,
diff stat y estado Git.

Criterio de aceptación: PD cerradas, base válida, usuario anterior a migraciones,
modelo completo, constraints, migraciones reproducibles y pruebas internas
aprobadas; fuentes intactas y pendientes documentados.

## Resultado real

PD01–PD09 cerradas; 14 modelos y cuatro migraciones iniciales generados/aplicados;
entorno mínimo aislado porque anfitrión usa Python 3.12. Django check,
makemigrations check y 59 pruebas internas pasaron tras corregir dos fallos
reales de preparación: Dockerfile mal formado y fixture run. Se añadieron
cuatro regresiones y rutina reproducible; resultados finales/commit están en
[FASE_MODELO.md](../evidencias/FASE_MODELO.md).

No importación ni UI/login/logout ni P01–P12. V2 motivada por validación omitida
en save/escrituras masivas, campos de procedencia y entorno anfitrión. No se
declara mejora de prompt: correcciones de código y fixtures no equivalen a una
iteración de instrucciones revisadas. Quedan tres temas/prompts mínimos por
ejecutar y dos mejoras con resultado comprobado.
