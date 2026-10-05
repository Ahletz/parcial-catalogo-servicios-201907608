# PROMPT-03 — revisión 1 por fallo observado

Fecha: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo/versión exacta: PENDIENTE DE REGISTRAR MANUALMENTE.
Prompt inicial: [P03_IMPORTACION.md](P03_IMPORTACION.md), solicitud del usuario.
Esta revisión técnica la formula el agente tras el fallo; no se atribuye al
usuario ni se cuenta como otro tema/prompt mínimo.

## Problema observado

La prueba real de 60 controles descubiertos ejecutó 44 y terminó con seis
errores. El validador heredado exige codigo aunque el campo de incidencia tiene
blank=True. Se pierden incidencias sin identidad y falla el cierre FALLIDA.
La inspección de campos/migraciones prevista en el prompt inicial no bastó para
detectar su interacción con validadores de la clase base.

## Prompt revisado utilizado para la corrección

~~~text
Continúa la implementación de importación conservando las restricciones originales.
Antes de persistir una entidad de evidencia, verifica la validación efectiva:
campos del modelo, metadatos blank/null y validadores heredados.

Una fila sin identidad N2 no tiene código de servicio: no inventes códigos,
no vincules un vecino y no cambies datos originales para eludir validación.
IncidenciaImportacion.codigo está aprobado como opcional (blank=True).
Corrige únicamente la contradicción del validador común con ese metadato.
Conserva la obligatoriedad de códigos/nombres/etiquetas en entidades que la exigen.
No cambies el esquema ni generes migraciones sin un cambio real de campos.

Mantén todos los tests y aserciones que revelaron el problema.
Repite exactamente la suite fallida y comprueba incidencias de 42/67,
rollback funcional y persistencia de FALLIDA. Después ejecuta la rutina
del modelo y P06/P07/P08; no declares aprobaciones hasta observar código 0.
Documenta cambio, archivos, resultados y limitaciones en contexto/evidencia.
~~~

## Resultado comprobado

La misma suite pasó después del ajuste: 60 tests en 46.420s, código 0.
P06/P07/P08 también pasaron: 3 tests en 8.214s, código 0. La revisión precedió
al cambio y fue leída por el agente antes de editar domain.py. El historial
y FASE_IMPORTACION identifican el commit y las rutinas finales. No se
presenta el fallo sintético de atomicidad como error de desarrollo.
