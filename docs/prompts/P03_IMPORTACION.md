# Prompt utilizado — IMPORTACIÓN

ID: PROMPT-03; no equivale al escenario oficial P03.
Fecha: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo/versión exacta: PENDIENTE DE REGISTRAR MANUALMENTE.
Base: b08a1e5. Tema obligatorio cubierto: IMPORTACIÓN.

## Objetivo y contexto suministrado

Implementar importador modular, idempotente y trazable del original y automatizar
P06/P07/P08. Se suministraron AGENTS, ENUNCIADO, V1/V2, REQUISITOS, ANALISIS_EXCEL,
DECISIONES, MODELO_DATOS, MATRIZ, modelos, migraciones y Git. Motivo: conservar
reglas aprobadas, conocer estructura real y evitar repetir/cambiar el modelo.

## Instrucciones realmente utilizadas

Extractos seleccionados de la solicitud adjunta del usuario:

~~~text
ROL:
Ingeniero senior de datos y desarrollador Django especializado en ETL, calidad de datos, trazabilidad e importaciones idempotentes.

OBJETIVO:
Implementar el importador completo de CatalogoServicios.xlsx utilizando los modelos y decisiones ya existentes, demostrar su idempotencia y automatizar los escenarios oficiales P06, P07 y P08.

Ejecuta primero la rutina actual:
bash scripts/verify-modelos.sh
y registra el resultado inicial.

Recuperar valores exclusivamente desde la celda principal de su rango combinado.
No realizar forward-fill genérico.

FILAS 42 Y 67:
NO deben crear servicios.
NO deben asignarse automáticamente al servicio anterior.
Debe conservarse la fila y contenido original relevante.

usar como nombre canónico:
"Suministrar Analitica"
conservar evidencia de:
"Suministrar Analitica"
"Mantener Tableros de Control"

asociar SE.12.3 con SE.12 mediante prefijo exacto y único del código;
registrar expresamente que esta asociación es una inferencia;

NO sobrescribir silenciosamente el valor humano;
conservar el nuevo valor proveniente del Excel en trazabilidad;
generar incidencia;

No debe dejar datos funcionales parcialmente importados ante un fallo fatal.

NO modificar ENUNCIADO.md.
NO modificar data/CatalogoServicios.xlsx.
NO implementar todavía login/logout.
NO implementar todavía interfaz completa.
NO leer ni mostrar secretos.
NO subir cambios al remoto.
~~~

La solicitud también exige conservar NULL/S/N/umbrales/códigos y etiquetas,
cargar todas las opciones, registrar procedencia persistente, 26 controles
mínimos, harness Docker/PostgreSQL, hashes antes/después y resultados reales.

## Salida y aceptación

Salida: archivos, arquitectura, reglas/casos reales, comando y dos ejecuciones,
contadores, P06–P08, hashes, pruebas/fallos/correcciones, contexto y prompts,
pendientes, commits locales, diff, status y log.

Aceptación: 12 N1/46 N2 sin duplicados; SE.12 y fila 101 trazables, 42/67
observadas, NULL y opciones originales conservadas, divergencias humanas
protegidas, atomicidad, P06–P08 automatizadas/aprobadas, regresiones del modelo
aprobadas y fuentes intactas. P01–P05/P09–P12 permanecen pendientes.

## Resultado e iteraciones

Lector/persistencia: 60 pruebas aprobadas; P06/P07/P08: tres aprobadas.
CLI original real: primera 76 creados; segunda cero creados/actualizados y
76 omitidos; ambas 12 N1/46 N2/18 opciones y cuatro incidencias por ejecución.
Resultados finales/commit: FASE_IMPORTACION.
Ocurrió una revisión de instrucciones por un fallo real de validación heredada:
[P03_REVISION_INTEGRIDAD.md](P03_REVISION_INTEGRIDAD.md).
Es una revisión del mismo prompt, no otro tema ni una nueva solicitud del usuario.
