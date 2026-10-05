# Evidencia de funcionalidad web

Fecha: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo/versión exacta: PENDIENTE DE REGISTRAR MANUALMENTE.
Base: f034c5af968dae920c94377c383095d5a7d98b29, main, árbol inicial limpio.
Se leyeron completos AGENTS, enunciado, V3, decisiones, modelo, matriz y
evidencias de modelo/importación; requisitos/análisis Excel según AGENTS.
Se inspeccionaron modelos, validadores, settings, Docker y pruebas existentes.
Motivo: aplicar reglas existentes y conservar 126 controles aprobados.
No repetir suites completas durante desarrollo; solicitud expresa del usuario.
Decisiones D20–D23 documentadas antes de implementar. No V4 ni dependencias nuevas.

## Integridad inicial

sha256sum ENUNCIADO.md data/CatalogoServicios.xlsx, código 0:

~~~text
c99201ed3e60aadbed9c7bebbfcc970290e6d13287eec0cbac984d01a0d55cfa  ENUNCIADO.md
de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0  data/CatalogoServicios.xlsx
~~~

Resultados observados y fallos conservados en las secciones siguientes.
P12 permanece pendiente. No push/tag ni lectura de .env reales/credenciales.

## Desarrollo y fallos reales

check inicial y check tras crear rutas: sin problemas, cero silenciados, código 0.
AST de 44 Python válido, código 0. build modelos con estáticos: código 0.
Comando dirigido inicial (sin repetir suite completa):

~~~bash
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_web_acceptance --keepdb --verbosity 2
~~~

Resultado: Ran 8 tests in 2.301s, FAILED (failures=2), código 1.
- P02: AssertionError: '_auth_user_id' unexpectedly found in SessionStore.
  Acceso inactivo sí se rechazaba; ModelBackend devuelve AnonymousUser sin
  limpiar los datos de autenticación de la sesión. La guarda solo llamaba logout
  si request.user era autenticado; falta invalidar la sesión autenticada residual.
- P05: esperaba texto "ya existe"; Django devolvió "Ya existe Empresa con este
  Codigo.". Duplicado rechazado correctamente; ajuste de capitalización de la
  aserción, conservando comprobaciones de error y cantidad persistida.

No fallos deliberados. La revisión de instrucciones sobre P02 se registra y
se lee antes de corregir la guarda; no se presenta P05 como mejora de prompt.
Un parche documental posterior falló por contexto esperado mal escrito
("Gu arda" en vez de "Guarda"); no alteró archivos. Se corrigió el contexto y
se aplicó el parche. No es fallo de aplicación ni otra mejora de prompt.

Fallo posterior del perfil local: los tres curl a /login/, /static/app.css y /
retornaron código 7/HTTP 000, conexión rechazada. Gunicorn sí estaba escuchando;
HostConfig.PortBindings solicitaba 127.0.0.1:8000, pero docker port no mostró
salida y NetworkSettings.Ports estaba vacío con el contenedor ejecutándose.
Causa: herencia exclusiva de red internal. D25 concreta bridge adicional solo
para web y control dirigido del puerto. No se presenta como otra mejora de prompt.
Antes del ajuste, urllib desde --network host también produjo URLError/
ConnectionRefusedError, código 1. Después de habilitar bridge, el primer
verify-web-local falló con TimeoutError, código 1: la espera de arranque solo
capturaba URLError y no el timeout directo de lectura. Corrección: reintentar
TimeoutError/ConnectionError dentro del mismo límite de 30 s. curl posterior
al arranque respondió 200 y docker port mostró 127.0.0.1:8000.

Corrección: accounts/access.py invalida cuando hay SESSION_KEY residual, además
de usuario autenticado inactivo. P05 conserva aserciones, con "Ya existe".
Se añadió regresión de cookie rechazada también después de reactivar.
La revisión técnica se leyó antes de editar y queda en P04_REVISION_SESIONES.

Controles dirigidos reales posteriores:

| Comando (prefijo docker compose -f compose.modelos.yaml run --rm modelos python manage.py test) | Resultado | Código |
|---|---|---|
| P02 y P05 por nombre completo, --keepdb --verbosity 2 | Ran 2 tests in 1.542s, OK. | 0 |
| tests.test_web_security tests.test_seed_demo --keepdb --verbosity 2 | Ran 26 tests in 8.294s, OK. | 0 |
| tests.test_web_maintenance --keepdb --verbosity 2, con --env-file .env.example | Ran 5 tests in 2.484s, OK. | 0 |

AST de 58 Python: válido/165 métodos test_, código 0. bash -n del nuevo harness
y git diff --check: código 0. Comparación Git contra base de originales, modelos,
domain.py, importador, dependencias y 126 tests anteriores: sin cambios, código 0.
No existía .env; se comprobó únicamente su existencia, sin leerlo. El harness
nuevo fuerza .env.example pública para no cargar secretos locales.

## Demostración HTTP/CLI anterior al commit

Comando: docker compose --env-file .env.example -f compose.modelos.yaml run --rm
modelos python /app/scripts/probe_funcional.py. Código 0. Nueva base conservada:
test_funcional_evidencia_5e4066daa0f6424088a0e241dc5d7bdf.
Migración/importación/seed/seed: códigos 0/0/0/0. Original conserva 12 N1/46 N2.
Primera demo: estructura creada 5, usuarios creados 2, asignaciones creadas 3.
Segunda: 0/0/0 creados y tres asignaciones válidas, sin duplicados.
Gunicorn HTTP real: CSS 200, anónimo redirigido a login, administrador accede
y crea empresa persistida, cinco páginas funcionales 200, sin CSRF 403,
cookie anterior rechazada tras logout, consulta lee 200 y escritura 403.
Las respuestas de login/alta siguen redirects y terminan en 200. No se confunden
con el código inicial de redirección. Credenciales efímeras generadas en memoria,
nunca impresas; base se conserva y servidor propio se termina en finally.
Excel antes/después igual al hash inicial. No es P12.

## Implementación y límites

accounts/forms.py/access.py: login, passwords editables sin exponer hash y
autorización en servidor. config/forms.py/web.py/urls.py: mantenimientos
explícitos, transacciones y mensajes; catalog/forms.py: filtros y nullable.
Templates y CSS local: navegación/rol, login, formularios/listados/ficha/bajas.
catalog/management/commands/seed_demo.py: demo con variables y rollback.
Compose: perfil funcional localhost:8000, sin publicar PostgreSQL. La imagen
prepara directorio estático; settings_test usa archivos locales sin manifiesto.
STORAGES funcional de settings.py conserva manifiesto para Docker final.
Web usa actualmente el entorno interno; despliegue final/P12 se difieren.
README, AGENTS, decisiones y matriz actualizados; prompt autenticación/revisión.
No V4, cambios de esquema, migraciones, dependencias ni modificaciones del lector.

39 nuevos escenarios: ocho oficiales HTTP, 19 seguridad, cinco mantenimientos,
siete seed; junto con 126 anteriores, 165 escenarios distintos previstos para
la única ejecución completa final. No contar probes/subTest como métodos extra.
Pruebas Django: integración en test_catalogo_modelos con rollback. El probe
verifica CLI/HTTP real en base test_ nueva; sin navegador visual automatizado.

Pendientes exclusivos de cierre: P12, Docker final/clon limpio,
README/RESOLUCION finales, quinto tema pruebas/Docker, versión exacta de IA,
identificación final del integrante y acceso/entrega GitHub. Segunda mejora
real ya registrada; dos actualizaciones V2/V3 existentes. No push ni tag.

## Verificación final y commit probado

Controles terminados el 2026-10-04T22:25:32-06:00, America/Guatemala.
Código Django probado: c342ce6d1f00bb012e4ed51236d7ebc2102892f9.
Mensaje: feat: implementar autenticacion y funcionalidad web.
Antes/después de verify-funcional el árbol estaba limpio. Comando real:

~~~bash
bash scripts/verify-funcional.sh
~~~

Resultado global: código 0. Se ejecutó UNA sola invocación completa de tests
en esta fase. La corrección posterior afecta exclusivamente red del perfil web
y control operativo; src, tests, Dockerfile, requirements, probe_funcional y
verify-funcional permanecen idénticos al commit probado (git diff --exit-code 0).
Se verificó esa corrección con el subconjunto operativo afectado, sin repetir
las 165 pruebas. El segundo commit integra D25, su control y esta evidencia;
mensaje fix: habilitar web local y registrar verificacion funcional.

| Comprobación final real | Resultado | Código |
|---|---|---|
| build modelos, fuentes iniciales/finales y pip check | Construcción válida, fuentes íntegras, No broken requirements found. | 0 |
| manage.py check | System check identified no issues (0 silenced). | 0 |
| migrate --noinput | No migrations to apply. | 0 |
| makemigrations --check --dry-run | No changes detected. | 0 |
| Cuatro módulos nuevos dirigidos | Ran 39 tests in 9.645s, OK. | 0 |
| manage.py test tests --keepdb --verbosity 2 | Ran 165 tests in 78.045s, OK. | 0 |
| probe_funcional.py final | Migración/importación/seed/seed 0/0/0/0; CLI/HTTP real validado. | 0 |
| verify-web-local.sh repetido tras corregir espera | Login 200, CSS 200, anónimo 302. | 0 |
| curl en anfitrión tras ajuste, respuestas descartadas | /login/ 200; /static/app.css 200; / 302. | 0 |
| docker port web | 8000/tcp → 127.0.0.1:8000. | 0 |
| bash -n de ambas rutinas; git diff --check | Válidos, sin errores. | 0 |
| stop del perfil funcional | Web/db detenidos; bases/volumen conservados. | 0 |

165 métodos distintos aprobados: 126 regresiones + 39 nuevos. El paso dirigido
repite 39: son 204 ejecuciones en el harness final, no 204 escenarios distintos.
Controles auxiliares/probes/subTest no aumentan métodos. Ningún fallo conocido
queda pendiente en esta fase; los fallos intermedios están documentados arriba.

### Escenarios oficiales

| ID | Método test_ / resultado comprobado | Estado |
|---|---|---|
| P01 | P01_login_valido_e_invalido: identificación normalizada válida y rechazo inválido. | APROBADA |
| P02 | P02_sin_sesion_logout_cookie_anterior_e_inactivo: anónimo, cookie antigua e inactivo rechazados. | APROBADA |
| P03 | P03_consulta_lee_y_no_escribe: lectura permitida, POST directo 403 sin persistencia. | APROBADA |
| P04 | P04_jerarquia_completa_y_usuario_por_http: seis entidades creadas y relaciones recuperables. | APROBADA |
| P05 | P05_duplicado_y_referencia_inexistente_rechazados: formulario con mensaje y sin inválidos. | APROBADA |
| P09 | P09_crear_y_editar_umbrales_invalidos: ambos rechazos conservan DB y NULL/0. | APROBADA |
| P10 | P10_busqueda_filtros_combinaciones_y_paginacion: criterios/páginas coherentes. | APROBADA |
| P11 | P11_responsable_otra_seccion_rechazado: inconsistencia rechazada y asignación válida aceptada. | APROBADA |

P06/P07/P08 pasaron nuevamente como REGRESIONES del importador aprobado,
sin declararlas nuevas. P06 ejecución temporal 70, P07 71/72: 12/46,
segunda cero creados/actualizados y 76 omitidos. P08 conservó canónico,
evidencia de ambos nombres, códigos textuales, inferencia y NULL.
Esos datos TestCase se revierten. P12 es el único escenario oficial pendiente.

### Demo final persistente y HTTP real

Nueva base conservada: test_funcional_evidencia_adbdf1c530684c0eb1b05e27b00e4db4.
Primera demo: estructura creada 5, usuarios creados 2, asignaciones creadas 3,
asignaciones válidas 3. Segunda: creados 0/0/0, válidas 3. Usuarios admin.demo
(ADMINISTRADOR) y consulta.demo (CONSULTA), ambos con variables demo sintéticas
efímeras. No se imprimen ni se registran passwords/cookies/hashes de usuarios.
Original: 12 N1, 46 N2, sin alteración por demo.
HTTP real de Gunicorn: login de ambos roles, cinco páginas funcionales,
CSS/lectura 200, alta administrativa persistida, falta de CSRF 403,
cookie tras logout rechazada y escritura de CONSULTA 403 sin dato nuevo.
Datos conservados para consulta; no lectura/alteración de otras bases.

### Integridad después de todos los controles

SHA-256 inicial = final, comando sha256sum con código 0:

~~~text
ENUNCIADO.md: c99201ed3e60aadbed9c7bebbfcc970290e6d13287eec0cbac984d01a0d55cfa
data/CatalogoServicios.xlsx: de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0
~~~

Configuración/control de red finalmente verificados (SHA-256):

~~~text
compose.modelos.yaml: 41eb4411a057b297b705524c248a33fd1f1283bdf4ee4b20902ceb89d0d7974f
scripts/verify-web-local.sh: bb53bfb464e8128bb28760749872b93e0c99758838632dc038522e01475eb976
~~~

Inventario de fase: 30 archivos nuevos y 10 modificados; fuente de detalle:
git diff --stat f034c5a HEAD. Nuevos principales: forms/access/web, templates y
CSS, seed_demo, cinco archivos de pruebas, probe/rutinas y tres documentos.
Modificados: .env.example, AGENTS, README, Dockerfile.modelos, Compose,
decisiones/matriz y settings/settings_test/urls. No modelos ni migraciones nuevos.
Identidad del segundo commit: git log -1 --format='%H %s' al cerrar; no escribir
un SHA propio ficticio antes de existir. Se conservan ambas bases de evidencia,
volumen y contenedores detenidos. No push/tag/reset/rebase ni secretos reales.
