# Evidencia de fase CMDB

Fecha: 2026-10-29, America/Guatemala. Base 396aa81.
Alcance: fuentes/modelo/relaciones/migración; sin CI generados/importados ni tests.

## Ubicación y limitación de entorno

El original /home/alex/Escritorio/parcial-catalogo-servicios-201907608 conserva
396aa81 y los tres duplicados sin seguimiento. El aislamiento rechazó escritura
(EROFS) incluso tras permisos; el ejecutor principal falló montando el socket
como directorio y Docker devolvió EPERM. No se modificaron contenedores/volúmenes.

Se clonó 396aa81 en
/home/alex/Documents/Codex/2026-10-29/anal/work/cmdb-model/checkout.
Los cambios y hasta dos commits se crean **en esa copia**, no en el original.
Se entrega parche/bundle para recuperar el trabajo. No presentar el código
preparado como aplicación efectiva al original.

La red del ejecutor tampoco resolvió PyPI. El navegador descargó desde PyPI
oficial Django 5.2.17, asgiref 3.12.1, sqlparse 0.6.0 y psycopg 3.3.6; pip
offline --no-deps los instaló solo en work/cmdb-model/runtime. Sin cambios a
requirements ni al runtime global. Se usó Python 3.12 del bundle de la sesión,
no se afirma ejecución de la imagen Python 3.13 ni de PostgreSQL 17.

## Configuración sintética de comprobación

PYTHONPATH apunta al runtime temporal, src y raíz de la copia.
DJANGO_SETTINGS_MODULE=config.settings; DJANGO_SECRET_KEY sintética pública;
DB_NAME=test_cmdb_modelo, DB_USER=cmdb_modelo, DB_PASSWORD vacío, DB_HOST apunta
a work/cmdb-model/sin-postgres (sin servidor), DB_PORT=5432.
No se leyó .env ni credenciales. No se usa SQLite, backend simulado ni
supresión de advertencias para fingir validación PostgreSQL.

## Comandos reales y resultados

Ejecutados mediante subprocess con argumentos separados, desde src de la copia:

~~~text
python -B manage.py check
Código: 0
System check identified no issues (0 silenced).

python -B manage.py makemigrations cmdb --noinput
Código: 0
Migrations for 'cmdb':
  cmdb/migrations/0001_initial.py
Seis modelos, dos índices CI, cuatro constraints explícitos, relaciones/FK.
Sin RunPython, semillas ni inserción de ejemplos.

python -B manage.py makemigrations --check --dry-run
Código: 0
No changes detected
~~~

Generación y dry-run emitieron RuntimeWarning: no se pudo consultar historial
consistente de migraciones porque no hay conexión al socket PostgreSQL de
aislamiento. Se preservó la advertencia. **Migración no aplicada**; historia,
constraints efectivos en PostgreSQL, ciclos y concurrencia no demostrados por
estos comandos. El check estático no sustituye pruebas de guardas.

## Revisiones y límites

Originales SHA en FUENTES_SERVICE_DESK/ANALISIS_CMDB; comparar antes/después.
Revisión estática: bosque independiente de organigrama; JSON por clase; fechas/
números/IP tipados; sin niveles semilla; Usuario FK; ServicioCI M:N; ciclos
técnicos del subgrafo restrictivo; flags históricos protegidos; referencias
activas y bajas por DomainModel existente. Sin normalización silenciosa de
extremos en saves parciales.

Los controles finales de AST/enlaces/diff/hashes y la lista de commits reales
se completan al cerrar la copia. No se ejecuta ningún método test_, suite,
P01–P18, generador, importador, seed_demo ni recorrido completo de impacto.
Los errores de permisos, descargas y revisión de código no se presentan como
un ciclo funcional de Loop ni como una mejora comprobada de prompt.

## Recuperación de los dos commits en la copia

~~~bash
git log --oneline 396aa81..HEAD
git log -1 --diff-filter=A --format='%H %s' -- docs/ANALISIS_CMDB.md
git log -1 --diff-filter=A --format='%H %s' -- src/cmdb/models.py
~~~

El resumen entregable registra hashes efectivamente creados; no inventar SHA
autorreferentes. No push/tag. La taxonomía adicional sigue sin fuente y la
aceptación exhaustiva de jerarquía no se declara cerrada.

## Controles finales observados

AST de los seis archivos Python CMDB correcto; migración con seis CreateModel y sin RunPython. Enlaces locales de documentos afectados correctos; hashes de CMDB.xlsx, CatalogoServicios.xlsx, Leccion_22.pdf y Tarea_Service_Desk.pdf intactos. git diff --check: código 0. Diff sin cambios en accounts/organization/catalog/imports/config.domain, tests, scripts, requirements o Docker/Compose. La única integración es añadir cmdb a INSTALLED_APPS. No son pruebas de ejecución de reglas.

Primer commit real en la copia: 2fb2521c8b1fb9aaeed29da99cb7e6a0c436f46a (documentación). Segundo commit identificable por git log de src/cmdb/models.py; el resumen de entrega registra su SHA real tras crearlo. No se afirma aceptación completa de esta fase en el repositorio original.
