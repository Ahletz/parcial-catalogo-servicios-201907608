# Catálogo de servicios — modelos e importación

Proyecto individual de Software Avanzado. Nombre/carné del integrante:
pendientes de confirmar para la entrega. Contexto inicial: f5f39e3.

Estado actual: base Django, usuario personalizado, organización, catálogo,
procedencia e importador modular idempotente. P06/P07/P08 automatizadas y
aprobadas; P01–P05/P09–P12 pendientes. No hay interfaz, login/logout ni demo.
Este entorno no sustituye el
despliegue final requerido con docker compose up --build -d.

## Ejecutar esta fase

Requisitos del anfitrión: Docker Engine y Docker Compose V2; Bash para el script.
Verificado con Engine 28.3.3 y Compose 2.39.1. No necesita Python, Django,
PostgreSQL ni dependencias instalados fuera de contenedores.

~~~bash
bash scripts/verify-modelos.sh
bash scripts/verify-importacion.sh
~~~

Ambos scripts construyen Python 3.13, inician PostgreSQL 17 aislado y verifican
fuentes/dependencias/configuración/migraciones. verify-modelos ejecuta sus 63
regresiones; verify-importacion ejecuta 60 controles de parser/persistencia,
P06/P07/P08 individualmente y dos invocaciones CLI en una BD test_ nueva.
Devuelven 0 si todos los controles pasan; cualquier fallo detiene con no 0.
El original está montado de solo lectura; su SHA-256 se verifica antes/después.

También puede ejecutarse cada comando del script por separado. Para generar
migraciones ante cambios futuros autorizados, usar la identidad del anfitrión:

~~~bash
docker compose -f compose.modelos.yaml run --rm --user "$(id -u):$(id -g)" modelos python manage.py makemigrations organization accounts catalog imports
docker compose -f compose.modelos.yaml run --rm modelos python manage.py migrate --noinput
docker compose -f compose.modelos.yaml run --rm modelos python manage.py makemigrations --check --dry-run
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_models --keepdb --verbosity 2
docker compose -f compose.modelos.yaml logs db
docker compose -f compose.modelos.yaml stop
~~~

No se publican puertos ni URL de aplicación en esta fase. El volumen
catalogo-modelos-201907608_datos_modelos conserva las bases catalogo_modelos y
test_catalogo_modelos; las pruebas usan únicamente esta última y transacciones
de rollback. --keepdb evita eliminarla al finalizar. No usar down -v ni apuntar
esta configuración a datos de evaluación.

## Importación y consulta de evidencia

Comando funcional disponible, para la base configurada en el contenedor:

~~~bash
docker compose -f compose.modelos.yaml run --rm modelos python manage.py import_catalog --file /app/data/CatalogoServicios.xlsx
~~~

Las verificaciones automatizadas no usan la base normal para importar datos de
prueba. Las pruebas Django usan test_catalogo_modelos y rollback. La demostración
CLI crea test_importacion_evidencia_UUID, migra allí y ejecuta dos importaciones;
conserva la base y muestra su nombre exacto junto con resultados/contadores.
Cada repetición genera otra base test_ sin borrar las anteriores.

Para consultar posteriormente esa evidencia, sustituir UUID_DEL_REPORTE por el
nombre mostrado y ejecutar mediante el mismo Compose:

~~~bash
IMPORT_DB=test_importacion_evidencia_UUID_DEL_REPORTE
docker compose -f compose.modelos.yaml run --rm -e DB_NAME="$IMPORT_DB" -e DB_TEST_NAME=test_consulta_evidencia modelos python manage.py shell -c "from imports.models import EjecucionImportacion, RegistroOrigen, IncidenciaImportacion; print(EjecucionImportacion.objects.count(), RegistroOrigen.objects.count(), IncidenciaImportacion.objects.count())"
~~~

Primera importación original: 12 N1, 46 N2, 18 opciones creadas, cuatro unidades
observadas/cuatro incidencias. Segunda: cero creados/actualizados, 76 omitidos,
cuatro observados/cuatro incidencias nuevas. Dos ejecuciones dejan 152 orígenes
y ocho incidencias; los contadores distinguen entidades y 97 filas físicas.

Arquitectura: parser lee bytes/hoja/celdas y clasifica filas; normalizer aplica
NULL/S/N/Decimal, opciones y reglas SE.12/prefijo; importer reconcilia y persiste
atómicamente; traceability escribe snapshots/incidencias; el comando solo
orquesta y muestra JSON. Los servicios están en src/imports/services.

Las ediciones humanas divergentes se conservan comparando por campo contra el
último snapshot IMPORTADO, y se registran nueva fuente/valor actual/incidencia.
No se modifican asignaciones organizacionales ni se reactivan N1/catálogos.
Los fallos revierten datos funcionales y conservan ejecución FALLIDA/incidencia.

La red interna del entorno modelo usa autenticación trust exclusivamente para
sus datos sintéticos y no contiene contraseñas reales. No reutilizarla como
configuración funcional final; esa configuración requerirá variables locales
según [.env.example](.env.example). Django nunca lee archivos .env por sí mismo.
La clave sintética del Compose solo pertenece a este entorno aislado.

## Dominio y documentación

- [AGENTS.md](AGENTS.md): contexto vigente, límites y comandos.
- [DECISIONES.md](docs/DECISIONES.md): cierre PD01–PD09.
- [MODELO_DATOS.md](docs/MODELO_DATOS.md): esquema y restricciones.
- [MATRIZ_TRAZABILIDAD.md](docs/MATRIZ_TRAZABILIDAD.md): avance parcial y aceptación pendiente.
- [CONTEXTO_V2.md](docs/contexto/CONTEXTO_V2.md): hallazgos reales que amplían V1.
- [CONTEXTO_V3.md](docs/contexto/CONTEXTO_V3.md): integridad efectiva de evidencia.
- [FASE_MODELO.md](docs/evidencias/FASE_MODELO.md): comandos, resultados, fallos y commit probado.
- [FASE_IMPORTACION.md](docs/evidencias/FASE_IMPORTACION.md): importaciones, P06–P08 y correcciones.

Escribir mediante save()/objects.create() y desactivar() en modelos de dominio.
update/bulk_create/bulk_update/delete se rechazan para evitar omitir reglas.
SQL directo/save_base no son APIs de negocio autorizadas; las pruebas los usan
deliberadamente solo para verificar constraints locales en test_.

Hay 126 pruebas distintas: 63 de modelo, 60 de importación y tres oficiales.
Las del modelo no sustituyen aceptación HTTP/UI. P06/P07/P08 usan el original;
los otros nueve P siguen pendientes. El contrato del lector está limitado a
Servicios Externos/A4:L4/5–101/E112:H122. Fórmulas en esas regiones se rechazan
sin evaluar/cachear. Umbrales que exceden Decimal(20,6) fallan sin redondear.
El lock común serializa escrituras; un servidor inaccesible puede impedir
registrar el propio fallo. La evidencia es consultable vía ORM; UI es futura.
La siguiente fase debe implementar autenticación/interfaz, demo,
despliegue Docker final y aceptación/documentación/GitHub completos.
