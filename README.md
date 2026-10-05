# Catálogo de servicios — base de modelos

Proyecto individual de Software Avanzado. Nombre/carné del integrante:
pendientes de confirmar para la entrega. Contexto inicial: f5f39e3.

Estado actual: base Django, usuario personalizado, organización, catálogo,
procedencia, migraciones y pruebas internas. No hay interfaz, login/logout,
importador ni demo; P01–P12 permanecen pendientes. Este entorno no sustituye el
despliegue final requerido con docker compose up --build -d.

## Ejecutar esta fase

Requisitos del anfitrión: Docker Engine y Docker Compose V2; Bash para el script.
Verificado con Engine 28.3.3 y Compose 2.39.1. No necesita Python, Django,
PostgreSQL ni dependencias instalados fuera de contenedores.

~~~bash
bash scripts/verify-modelos.sh
~~~

El script construye Python 3.13, inicia PostgreSQL 17 aislado, verifica fuentes,
dependencias, configuración, migraciones y pruebas del modelo. Devolverá 0 si
todos los controles pasan; cualquier fallo interrumpe la rutina con código no 0.
No importa el Excel: solo compara su SHA-256 y lo monta de solo lectura.

También puede ejecutarse cada comando del script por separado. Para generar
migraciones ante cambios futuros autorizados, usar la identidad del anfitrión:

~~~bash
docker compose -f compose.modelos.yaml run --rm --user "$(id -u):$(id -g)" modelos python manage.py makemigrations organization accounts catalog imports
docker compose -f compose.modelos.yaml run --rm modelos python manage.py migrate --noinput
docker compose -f compose.modelos.yaml run --rm modelos python manage.py makemigrations --check --dry-run
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests --keepdb --verbosity 2
docker compose -f compose.modelos.yaml logs db
docker compose -f compose.modelos.yaml stop
~~~

No se publican puertos ni URL de aplicación en esta fase. El volumen
catalogo-modelos-201907608_datos_modelos conserva las bases catalogo_modelos y
test_catalogo_modelos; las pruebas usan únicamente esta última y transacciones
de rollback. --keepdb evita eliminarla al finalizar. No usar down -v ni apuntar
esta configuración a datos de evaluación.

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
- [FASE_MODELO.md](docs/evidencias/FASE_MODELO.md): comandos, resultados, fallos y commit probado.

Escribir mediante save()/objects.create() y desactivar() en modelos de dominio.
update/bulk_create/bulk_update/delete se rechazan para evitar omitir reglas.
SQL directo/save_base no son APIs de negocio autorizadas; las pruebas los usan
deliberadamente solo para verificar constraints locales en test_.

Las pruebas internas cubren el modelo, no sesiones HTTP, interfaz, importación
del original ni persistencia entre reinicios; no equivalen a P01–P12.
La siguiente fase debe implementar importador, autenticación/interfaz, demo,
despliegue Docker final y aceptación/documentación/GitHub completos.
