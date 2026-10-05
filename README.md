# Catálogo de servicios — aplicación funcional

Proyecto individual de Software Avanzado. Nombre/carné del integrante:
pendientes de confirmar para la entrega. Contexto inicial: f5f39e3.

Estado actual: login/logout local, roles en servidor, mantenimientos de
organización/usuarios/N1/N2/clasificaciones, filtros/paginación, ficha completa,
responsables, importador y demo idempotente. P01–P11 automatizadas; P12 pendiente.
Este entorno no sustituye el
despliegue final requerido con docker compose up --build -d.

## Ejecutar esta fase

Requisitos del anfitrión: Docker Engine y Docker Compose V2; Bash para el script.
Verificado con Engine 28.3.3 y Compose 2.39.1. No necesita Python, Django,
PostgreSQL ni dependencias instalados fuera de contenedores.

## Revisar la aplicación local

Copiar .env.example a .env y configurar localmente DEMO_ADMIN_PASSWORD y
DEMO_CONSULTA_PASSWORD con contraseñas de demostración distintas y no triviales.
Los identificadores predeterminados son admin.demo y consulta.demo; se pueden
cambiar mediante DEMO_ADMIN_IDENTIFICADOR/DEMO_CONSULTA_IDENTIFICADOR.
Nunca versionar .env. Esta vista usa el Compose interno y datos de demostración;
el despliegue final con configuración propia y P12 corresponde al cierre.

~~~bash
docker compose --env-file .env -f compose.modelos.yaml build modelos
docker compose --env-file .env -f compose.modelos.yaml up -d db
docker compose --env-file .env -f compose.modelos.yaml run --rm modelos python manage.py migrate --noinput
docker compose --env-file .env -f compose.modelos.yaml run --rm modelos python manage.py import_catalog --file /app/data/CatalogoServicios.xlsx
docker compose --env-file .env -f compose.modelos.yaml run --rm modelos python manage.py seed_demo
docker compose --env-file .env -f compose.modelos.yaml --profile funcional up --build -d web
~~~

URL: http://localhost:8000/login/. Entrar con cada identificador y la contraseña
configurada localmente. ADMINISTRADOR puede crear/editar/desactivar; CONSULTA
solo lee. Usuario y rol aparecen en la cabecera. Logout es POST con CSRF;
sesiones previas de inactivos se invalidan al intentar acceso protegido.

La organización mantiene Empresa → Área → Departamento → Sección → Puesto →
Usuario. Los formularios no permiten huérfanos ni padres inactivos; las bajas
bloquean dependencias activas/desconocidas y conservan información histórica.
Servicios permite código/nombre, N1/estado/clase/criticidad/tipo y paginación de
20 registros. Estado desconocido es distinto de inactivo. La ficha muestra
todos los atributos; los responsables se editan en el formulario del servicio.

seed_demo crea cinco unidades y dos roles, y asigna tres importados disponibles.
Repetirlo no rota contraseñas, no sobrescribe asignaciones ni reactiva bajas.
Si faltan importados sin asignación, falla con rollback e indica importar primero.
Una cuenta demo existente con otro rol/puesto/estado requiere revisión explícita.
Para cambiar una contraseña existente, editar el usuario como administrador o
usar el comando Django changepassword; dejarla vacía en edición la conserva.

~~~bash
docker compose --env-file .env -f compose.modelos.yaml logs web db
docker compose --env-file .env -f compose.modelos.yaml --profile funcional stop
~~~

Para iniciar de nuevo sin borrar datos: up -d db y --profile funcional up -d web
con los mismos archivos/variables. Este procedimiento aún no constituye P12.

## Verificación funcional completa

~~~bash
bash scripts/verify-funcional.sh
bash scripts/verify-web-local.sh
~~~

El script fuerza .env.example pública, sin leer .env reales; construye, migra,
comprueba fuentes/configuración/dependencias y migraciones pendientes. Ejecuta
39 pruebas HTTP/demo dirigidas y una única invocación completa de las 165 pruebas,
incluidas las 126 anteriores y P01–P11. Devuelve 0 solo si todo pasa.
Durante desarrollo ejecutar únicamente el módulo/método afectado con manage.py
test y --keepdb; no repetir la suite completa tras cada cambio.

Además crea test_funcional_evidencia_UUID, importa el original, ejecuta seed_demo
dos veces y comprueba HTTP real con Gunicorn, CSS local, ambos roles, CSRF,
escrituras y cookie tras logout. Sus credenciales sintéticas son efímeras y no
se imprimen. Base y volumen se conservan; ninguna prueba escribe en catalogo_modelos.
Las pruebas Django usan test_catalogo_modelos y rollback. La UI de revisión
local utiliza catalogo_modelos; no es la base de los tests.
verify-web-local comprueba el perfil publicado desde el anfitrión Docker:
login/CSS 200 y acceso anónimo 302, sin imprimir tokens ni modificar registros.
Solo web participa además en una red de interfaz para publicar localhost:8000;
PostgreSQL y el runner de pruebas conservan la red interna.

Pruebas de modelo/importación anteriores, si se necesitan por cambios en esas capas:

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

PostgreSQL no publica puertos; el perfil funcional publica solo localhost:8000.
El volumen
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

La red interna de revisión usa autenticación trust para sus datos sintéticos.
El despliegue final tendrá configuración independiente mediante variables locales
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
- [FASE_FUNCIONAL.md](docs/evidencias/FASE_FUNCIONAL.md): HTTP/demo, P01–P05/P09–P11 y correcciones.

Escribir mediante save()/objects.create() y desactivar() en modelos de dominio.
update/bulk_create/bulk_update/delete se rechazan para evitar omitir reglas.
SQL directo/save_base no son APIs de negocio autorizadas; las pruebas los usan
deliberadamente solo para verificar constraints locales en test_.

Hay 165 pruebas distintas: 126 anteriores y 39 nuevas HTTP/demo, con ocho
oficiales nuevas. P06/P07/P08 usan el original y son regresiones de esta fase;
P12 es el único escenario oficial pendiente. El contrato del lector está limitado a
Servicios Externos/A4:L4/5–101/E112:H122. Fórmulas en esas regiones se rechazan
sin evaluar/cachear. Umbrales que exceden Decimal(20,6) fallan sin redondear.
El lock común serializa escrituras; un servidor inaccesible puede impedir
registrar el propio fallo. La evidencia es consultable vía ORM; UI es futura.
La siguiente fase debe cerrar Docker reproducible desde clon limpio, P12,
README/RESOLUCION finales, quinto tema de prompts y acceso/entrega GitHub.
