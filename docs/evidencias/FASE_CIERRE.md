# Evidencia de cierre final

Fecha: 2026-10-04, America/Guatemala. Inicio observado: 22:37:23.
Herramienta: Codex en VS Code; familia indicada GPT-6; versión exacta:
PENDIENTE DE REGISTRAR MANUALMENTE.
Base: 140af56c804ef4086637c1ea2c2af404e5b14327, main.
Estado inicial: origin/main [gone]; PDF sin seguimiento, sin cambios propios.
origin: https://github.com/Ahletz/parcial-catalogo-servicios-201907608.git.
.env real ausente: comprobación de existencia, no lectura de contenido.

## Lectura y decisiones

Se leyeron AGENTS, ENUNCIADO, README, REQUISITOS, DECISIONES, MATRIZ,
CONTEXTO_V3, MODELO_DATOS y evidencias de modelo/importación/funcionalidad.
RESOLUCION no existía. Inspección de Docker, scripts, settings y .env.example.
D26–D30 registradas antes de implementar: imagen final, db/init/web,
aislamiento, recreación P12 y PDF excluido. No rehacer código aprobado.

## Integridad inicial

sha256sum, código 0:

~~~text
c99201ed3e60aadbed9c7bebbfcc970290e6d13287eec0cbac984d01a0d55cfa  ENUNCIADO.md
de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0  data/CatalogoServicios.xlsx
42691088199b23940cfd916b92d785c42246070feb35bef6430292f5074a7c6b  data/201907608_P2_SA.pdf
~~~

PDF considerado material adicional por nombre/ubicación; no exigido por §7,
no interpretado ni modificado. Se excluye de Git/build mediante regla precisa.
Versiones obtenidas con código 0: Engine 28.3.3; Compose 2.39.1.

## Cambios y controles de desarrollo

Dockerfile/compose.yaml finales, verify.sh, verify-persistence.sh y helpers
controlados; documentación final y quinto prompt. Mantienen src/tests,
requirements, modelos/migraciones/importador/autenticación/interfaz aprobados.
Imagen no root, collectstatic en build, PostgreSQL autenticado sin puerto
publicado, healthchecks y init de migraciones antes de web. Solo web participa
en bridge para localhost; no reset/import/demo automáticos al arrancar.

AST de Python, bash -n de scripts nuevos y git diff --check: código 0.
Inspección detectó que import_catalog antepone una línea al JSON y guarda
contadores en totales. Probe adaptado antes de ejecutarlo; no se presenta como
fallo real ni como una tercera mejora de prompt.

Resultados de P12 dirigido, ensayo limpio y harness final se completan con
salidas observadas después de ejecutarlos; no inferir aceptación de los archivos.

## Controles dirigidos reales antes del commit

bash scripts/verify-persistence.sh: código 0. Proyecto aislado
catalogo-qa-1791175333-206375; migraciones aplicadas y web healthy.
Dato antes/después: Empresa P12-PERSISTENCIA, PK=1, nombre idéntico; N1/N2=0/0
porque esta prueba dirigida solo crea su registro. db/web con IDs diferentes,
volumen catalogo-qa-1791175333-206375_datos_postgres idéntico. Sin eliminar datos.
El P12 final comprobará además catálogo importado 12/46.

Control dirigido nuevo probe: build/up/runner probe_final.py/stop, código 0.
Primera importación: 76 creados (12/46/2/5/11), cuatro observaciones/incidencias;
segunda: cero creados/actualizados, 76 omitidos. Demo primera: 5 unidades,
2 usuarios, 3 asignaciones válidas; segunda 0/0/0 y tres válidas. Gunicorn real
con DEBUG=false: ambos roles, lectura de cinco páginas, CSS, alta administrativa,
consulta escritura 403 y cookies rechazadas tras logout. Todo código 0.
No suites completas ejecutadas durante desarrollo.

Enlaces Markdown/AST/scripts/Git diff y comparación de src/tests/requirements
contra 140af56: código 0. No cambios en código aprobado. .env y PDF correctamente
ignorados, sin archivos secretos rastreados por nombre. Una corrección de typo
por apply_patch falló por contexto inexistente, sin modificar archivo; se usó
sustitución textual precisa. No se presenta como error de aplicación/IA prompt.

El commit técnico contiene el plan/documentación inicial; el segundo únicamente
registrará controles finales observados y estados documentales. Identidades
se obtienen de Git, sin anticipar SHA propios ficticios.
