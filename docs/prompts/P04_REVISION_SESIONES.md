# PROMPT-04 — revisión real de invalidación de sesiones

Fecha: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo/versión exacta: PENDIENTE DE REGISTRAR MANUALMENTE.
Inicial: [P04_AUTENTICACION_FUNCIONAL.md](P04_AUTENTICACION_FUNCIONAL.md).
Revisión técnica del agente, no una nueva solicitud atribuida al usuario.
Segunda mejora del proyecto; mismo tema AUTENTICACIÓN, no quinto tema.

## Problema observado

La primera ejecución oficial falló P02: el acceso de la cuenta inactiva se
rechaza, pero '_auth_user_id' continúa en SessionStore. ModelBackend presenta
AnonymousUser; la guarda que mira solo is_authenticated no invalida esa sesión.
La solicitud exige rechazar sesiones previas de inactivos; falta precisar la
limpieza efectiva de credenciales residuales, además de la respuesta HTTP.

## Instrucción revisada utilizada antes de corregir

~~~text
Continúa con el alcance y restricciones de la solicitud funcional original.
No asumas que AnonymousUser implica que la sesión ya carece de autenticación.
Al rechazar acceso protegido, si existe SESSION_KEY en la sesión o un usuario
autenticado no activo, llama logout para invalidar esa sesión en PostgreSQL.
No alteres ModelBackend, el modelo, el importador ni hashes/sesiones ajenos.
Mantén las aserciones P02 que detectaron datos de autenticación residuales.
Añade regresión: desactivar una cuenta con sesión, rechazar acceso, reactivarla
y comprobar que su antigua cookie sigue rechazada. Verifica sesión eliminada.
Repite únicamente P02 y P05 tras la corrección; conserva sus resultados reales.
Luego prueba seguridad HTTP dirigida y ejecuta la suite completa al cierre.
No imprimas cookies, contraseñas ni hashes. No crees V4 para este ajuste.
~~~

## Resultado

P02/P05 repetidas individualmente en el mismo comando: 2 tests en 1.542s,
código 0. Seguridad/demo: 26 tests en 8.294s, código 0, incluida cookie rechazada
después de reactivar y sesión eliminada. Instrucción registrada y leída antes
de editar la guarda. No se eliminaron aserciones de P02. Controles finales en
[FASE_FUNCIONAL.md](../evidencias/FASE_FUNCIONAL.md).
