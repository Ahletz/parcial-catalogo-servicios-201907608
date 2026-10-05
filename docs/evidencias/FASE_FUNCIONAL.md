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

Resultados y fallos se añadirán únicamente después de ejecutar sus controles.
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
