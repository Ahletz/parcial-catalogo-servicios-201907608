# Catálogo de servicios — Software Avanzado

Proyecto individual: parcial-catalogo-servicios-201907608. Carné: **201907608**.
Autor: **Aheltz** (nombre configurado en Git; nombre completo PENDIENTE DE CONFIRMAR).
Repositorio: https://github.com/Ahletz/parcial-catalogo-servicios-201907608.

Aplicación para mantener catálogo de servicios, organización y usuarios.
Autenticación local, roles ADMINISTRADOR/CONSULTA, bajas lógicas, búsqueda,
filtros, paginación y responsables. Monolito Django 5.2.17/Python 3.13.16,
PostgreSQL 17.11, Gunicorn y WhiteNoise; openpyxl importa el Excel original.
No requiere cuentas de IA ni claves de proveedores para funcionar.

## Flujo FINAL de evaluación

Los archivos definitivos son **Dockerfile y compose.yaml**. Los archivos
Dockerfile.modelos/compose.modelos.yaml se conservan para reproducir evidencia
histórica; no son necesarios para levantar la entrega final.

Requisitos del anfitrión: Git, Docker Engine y Compose V2. Bash para el harness
(en Windows, WSL o Git Bash). Versiones comprobadas: Engine 28.3.3 y Compose
2.39.1; no se afirma compatibilidad de versiones anteriores no probadas.
No instalar Python, Django ni PostgreSQL en el anfitrión.

~~~bash
git clone https://github.com/Ahletz/parcial-catalogo-servicios-201907608.git
cd parcial-catalogo-servicios-201907608
docker compose up --build -d
~~~

**No es obligatorio crear .env para evaluar.** compose.yaml define defaults con
sintaxis ${VARIABLE:-valor} exclusivamente para desarrollo/evaluación local:
son valores públicos, inseguros y **no deben usarse en producción**. No son
secretos reales.

| Variable | Default de evaluación (compose.yaml) |
|---|---|
| DJANGO_SECRET_KEY | django-insecure-evaluation-only-change-in-production |
| DB_PASSWORD | evaluacion-local-insegura-no-produccion |
| DEMO_ADMIN_IDENTIFICADOR / DEMO_ADMIN_PASSWORD | admin.demo / Evaluacion-Admin-Demo-2026 |
| DEMO_CONSULTA_IDENTIFICADOR / DEMO_CONSULTA_PASSWORD | consulta.demo / Evaluacion-Consulta-Demo-2026 |
| DB_NAME / DB_USER | catalogo / catalogo |
| DJANGO_DEBUG | false |
| DJANGO_ALLOWED_HOSTS | localhost,127.0.0.1 |
| DJANGO_SECURE_COOKIES | false (true solo al servir HTTPS) |
| APP_PORT | 8000 (cambiar si está ocupado) |

Para personalizar o desplegar fuera de evaluación, copiar la plantilla y
reemplazar los placeholders **antes del primer arranque**; los valores de .env
(o variables exportadas en la shell) tienen prioridad sobre los defaults:

~~~bash
cp .env.example .env   # opcional; editar localmente
~~~

No versionar .env (está en .gitignore) ni publicar sus valores. Docker Compose
suministra variables; Django no abre .env. No cambiar DB_PASSWORD/DB_USER sobre
un volumen ya inicializado esperando que se reconfigure PostgreSQL: requiere
gestión explícita. No usar docker compose config sin --quiet para evitar mostrar
configuración.

Este comando construye desde el código del repositorio, espera PostgreSQL healthy,
ejecuta migraciones en init y después inicia web. collectstatic se ejecuta al
construir la imagen; Gunicorn sirve la aplicación y WhiteNoise el CSS con DEBUG=false.
Web usa usuario no root. URL: **http://localhost:8000/login/**.
Solo localhost publica 8000; PostgreSQL no publica puerto al anfitrión.

Importación y cuentas demo son pasos explícitos, sin reset automático:

~~~bash
docker compose exec -T web python manage.py migrate --noinput
docker compose exec -T web python manage.py import_catalog --file /app/data/CatalogoServicios.xlsx
docker compose exec -T web python manage.py seed_demo
~~~

La migración explícita es repetible; init ya la aplicó en el arranque. Entrar
con admin.demo o consulta.demo y su contraseña (defaults de evaluación arriba o .env).
Administrador mantiene usuarios, jerarquía, N1/N2, clase, criticidad y tipo.
Consulta solo lee: las escrituras directas reciben HTTP 403. Logout es POST
con CSRF; cuentas inactivas y cookies anteriores invalidadas se rechazan.

El original importa 12 N1, 46 N2 y 18 opciones (2/5/11). Reimportar conserva
identidades y ediciones humanas divergentes, genera nueva trazabilidad y resumen
creados/actualizados/omitidos/observados. No modifica el Excel, montado ro.
seed_demo crea cinco unidades, dos roles y tres asignaciones válidas. Repetir
no duplica, no rota contraseñas ni sobrescribe asignaciones humanas. Para cambiar
una contraseña existente usar mantenimiento de usuario o changepassword.

## Pruebas y harness final

~~~bash
bash scripts/verify.sh
~~~

Rutina única: configuración pública sintética, proyecto catalogo-qa-TIMESTAMP-PID,
volumen independiente, PostgreSQL autenticado, migraciones, fuentes, pip check,
Django check, comprobación de migraciones, dos importaciones/demo, HTTP real,
UNA suite completa de 165 tests y P12. Publica temporalmente localhost:18000;
dejar ese puerto libre. Devuelve 0 solo si todo pasa; un fallo retorna distinto
de 0 y no se presenta como aprobación. Detiene contenedores al terminar y
conserva su volumen/base. Nunca lee .env real ni opera el volumen de evaluación.

P01–P11 son métodos Django en PostgreSQL test_catalogo_final, aislados mediante
transacciones; no se ejecutan sobre la base de evaluación. P12 es una prueba
operativa adicional: crea Empresa controlada, stop, up --force-recreate de
PostgreSQL/web, comprueba IDs diferentes, mismo volumen y mismo dato/PK/conteos.
Son **165 tests Django + un escenario operativo P12**, no 166 métodos Django.

P12 independiente, sin repetir la suite:

~~~bash
bash scripts/verify-persistence.sh
~~~

Crea su propio entorno sintético y lo deja iniciado para inspección. Para
reutilizar el proyecto mostrado y detenerlo:

~~~bash
export QA_PROJECT=catalogo-qa-TIMESTAMP-PID
source scripts/verify-common.sh
qa_compose stop
~~~

Pruebas dirigidas durante futuros cambios (solo el módulo afectado):

~~~bash
docker compose run --rm runner python manage.py test tests.test_web_acceptance --keepdb --verbosity 2
docker compose exec -T web python manage.py check
docker compose exec -T web python manage.py makemigrations --check --dry-run
~~~

Resultados verificables y commit probado: [FASE_CIERRE](docs/evidencias/FASE_CIERRE.md).
Las rutinas históricas de modelos/importación/funcionalidad se conservan para
reproducir sus fases; no ejecutarlas todas como parte del cierre actual.

## Logs, apagado, reinicio y recuperación

~~~bash
docker compose ps
docker compose logs --tail 100 web init db
docker compose stop
docker compose up -d
~~~

Apagado normal alternativo: docker compose down **sin -v**. Conserva el volumen
catalogo-servicios-201907608_datos_postgres; up --build -d recrea contenedores y
recupera los datos. Detener/recrear no vuelve a importar ni cambia contraseñas.
Para actualizar código, repetir up --build -d: init aplica migraciones pendientes.
Si el puerto está ocupado cambiar APP_PORT; si init falla revisar logs init y
configuración local antes de repetir up. No resolver fallos borrando el volumen.
La persistencia evita pérdida por recreación; no constituye copia de seguridad.

**Procedimiento destructivo, exclusivamente sobre un proyecto de pruebas
prescindible:** borra todos sus datos; nunca usar en P12 ni sobre evaluación.
Se documenta por §5, no se ejecuta en esta entrega.

~~~bash
docker compose --env-file .env.example -f compose.yaml -p PROYECTO_DE_PRUEBAS_CONFIRMADO down -v
~~~

Configurar las mismas variables sintéticas del harness antes de ese comando.
El proyecto debe identificarse y revisarse explícitamente; el apagado normal
siempre conserva volúmenes.

## Estructura y documentación

~~~text
Dockerfile, compose.yaml, .dockerignore, .env.example
src/config, accounts, organization, catalog, imports
src/templates, src/static
tests/                    165 pruebas Django
scripts/verify.sh          harness final
scripts/verify-persistence.sh  P12
data/CatalogoServicios.xlsx   original inmutable
docs/RESOLUCION.md         explicación técnica/DER/diccionario
docs/MATRIZ_TRAZABILIDAD.md cobertura individual y evidencias
docs/contexto/            V1, V2, V3
docs/prompts/             cinco temas y dos revisiones reales
docs/evidencias/          resultados de las cuatro fases
~~~

[RESOLUCION](docs/RESOLUCION.md), [matriz](docs/MATRIZ_TRAZABILIDAD.md),
[auditoría](docs/AUDITORIA_RUBRICA.md) y [AGENTS](AGENTS.md) permiten justificar
las decisiones. El PDF local es material adicional no exigido; permanece
fuera de Git/build y no se altera. La aplicación no evalúa instrucciones del
Excel; sus textos son datos no confiables y se muestran escapados.

## Entrega GitHub

Rama: main. Remoto esperado: https://github.com/Ahletz/parcial-catalogo-servicios-201907608.git.
origin/main [gone] describe una referencia local ausente; no demuestra que el
repositorio remoto haya desaparecido. Publicación normal, sin force:

~~~bash
git status --short --branch
git push -u origin main
git rev-parse HEAD
git tag parcial-v2.0
git push origin parcial-v2.0
~~~

No se ejecutaron push/tag durante el cierre. Crear etiqueta solamente después
de completar metadatos y confirmar el commit final, sin reutilizar otra etiqueta.
Agregar **maldanap-usac** en GitHub → Settings → Collaborators con acceso suficiente;
si privado, verificar invitación enviada y si está aceptada. No basta mencionarlo.
Entregar por el medio indicado: URL, nombre completo, carné 201907608, rama main,
SHA mostrado y etiqueta parcial-v2.0. Mantener el commit disponible durante
calificación. Nombre completo y versión exacta de IA requieren confirmación
manual; no se inventan. La auditoría distingue verificación local de entrega remota.
