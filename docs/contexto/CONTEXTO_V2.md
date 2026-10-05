# CONTEXTO V2 — guardas del modelo y entorno real

Fecha: 2026-10-04, America/Guatemala. Herramienta: Codex en VS Code.
Modelo/versión exacta: PENDIENTE DE REGISTRAR MANUALMENTE.
Contexto anterior: [CONTEXTO_V1.md](CONTEXTO_V1.md), commit f5f39e3.
Se registra una actualización real; no se crea V3 ni se acreditan dos cambios.

## Hallazgo, motivo y cambio

1. Django save() no llama full_clean() y update/bulk_create/bulk_update omiten
   métodos del modelo. Un clean() aislado, propuesto genéricamente en V1, no
   garantiza reglas al usar objects.create()/guardar desde futuros comandos.
   Reglas entre tablas (padre activo, responsable de sección, baja con
   dependientes) tampoco caben en un CHECK local.
2. El anfitrión tiene Python 3.12.3, no 3.13. Para cumplir stack y verificación
   PostgreSQL sin instalaciones anfitrión, hace falta un contenedor mínimo.
3. NULL en sección N2 no distingue excepción de importación frente a alta manual;
   timestamps solos no distinguen una modificación humana de reimportación.

Cambio: cerrar PD01–PD09, validar cada save en transacción, serializar escrituras
del dominio con advisory lock, bloquear escritura masiva/borrado físico y
retener CHECK/UNIQUE/FK locales. Añadir origen N2 y revision_manual/snapshots
para las excepciones y futuras comparaciones, sin implementar importador.
Crear entorno específico de modelos, sin web ni puertos públicos.

Alternativas: solo formularios/clean deja bypass; triggers cruzados añaden
complejidad al parcial; instalar Python/BD locales incumple reproducibilidad.
Se conserva monolito, stack, módulos, jerarquía y políticas aprobadas de V1.

Justificación técnica:
[validación Django](https://docs.djangoproject.com/en/5.2/ref/models/instances/),
[QuerySet](https://docs.djangoproject.com/en/5.2/ref/models/querysets/) y
[constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/).
La limitación material es serializar escrituras de negocio y exigir que
comandos futuros usen save/desactivar; SQL directo no valida reglas cruzadas.

## Fuentes suministradas al agente

Se leyeron completos AGENTS.md, ENUNCIADO.md, CONTEXTO_V1, REQUISITOS,
ANALISIS_EXCEL, DECISIONES y MATRIZ_TRAZABILIDAD, más la solicitud actual y Git.
Enunciado/requisitos delimitan alcance; análisis Excel protege datos/ausencias;
decisiones/matriz preservan acuerdos y pendientes. Se consultó documentación
oficial Django para el hallazgo y PyPI para versiones. El Excel solo se usó
para comprobar integridad; no se interpretó ni importó su contenido en esta fase.

## Impacto y archivos afectados

- Dominio compartido: src/config/domain.py.
- Modelos: src/accounts, organization, catalog e imports; cuatro migraciones 0001.
- Configuración: config/settings.py/settings_test.py, requirements, .env.example.
- Entorno mínimo: Dockerfile.modelos, compose.modelos.yaml, .dockerignore.
- Controles: tests/test_models.py, scripts/verify-modelos.sh/check_sources.py.
- Contexto: AGENTS, DECISIONES, MATRIZ, REQUISITOS, README y MODELO_DATOS.
- Evidencia: prompt de modelo y FASE_MODELO; V1 queda intacto como registro histórico.

## Validación y commit

Se generaron/aplicaron migraciones; check y makemigrations --check --dry-run
pasaron. La ejecución interna de 59 pruebas pasó después de corregir la fixture
run que ocultaba unittest.TestCase.run. Se añadieron cuatro regresiones para
normalización directa, origen histórico y constraints locales; el resultado
final y commit probado se registran en [FASE_MODELO.md](../evidencias/FASE_MODELO.md).

Commit asociado de esta actualización, mediante historial real:

~~~bash
git log -1 --format='%H %s' -- docs/contexto/CONTEXTO_V2.md
~~~

## Estado y pendientes

Modelo persistente implementado, no aplicación funcional completa. No hay
login/logout, UI, importador, demo ni P01–P12 ejecutadas. Sin alteraciones del
enunciado/Excel ni lectura de secretos. Falta V3 por nuevo hallazgo real, tres
prompts mínimos, dos mejoras de prompts y despliegue/aceptación/documentación
finales. Los fallos no deliberados de esta fase se conservan en la evidencia.
