# Evidencia — cierre de Service Desk

Fecha: 2026-10-29, America/Guatemala. Prompt
[SD-PE04](../prompts/SD_P04_CIERRE_GRAFOS_PRUEBAS_DOCKER.md).
Commit funcional verificado: `f15deb0` (`feat: completar portal consola cmdb
grafos y datos demo de Service Desk`), rama `main`.

Este documento registra **solo resultados realmente obtenidos**. No se
declara aprobada ninguna prueba cuya ejecución no concluyó.

## 1. Entorno

- Linux; Docker Compose con imagen del proyecto.
- Python 3.13.16 (contenedor `web`); PostgreSQL 17.
- Mediciones HTTP con `django.test.Client` dentro del contenedor `web`.
- Configuración sintética del harness; `.env` real no leído ni publicado.

## 2. Bloque A — construcción y controles estáticos

| Control | Resultado |
|---|---|
| Docker build | Correcto |
| PostgreSQL | healthy |
| web | healthy |
| Integridad `ENUNCIADO.md` | Correcta (hash coincide) |
| Integridad `data/CatalogoServicios.xlsx` | Correcta (hash coincide) |
| `pip check` | Correcto |
| `manage.py check` | System check identified no issues. |
| `manage.py makemigrations --check --dry-run` | No changes detected |

Código de salida del bloque: **EXIT=0**.

## 3. Bloque B1 — datos, HTTP, CMDB y demo

### Catálogo (SD-P02 operativo)

| Medida | Resultado |
|---|---|
| N1 | 12 |
| N2 | 46 |
| Primera importación | Correcta |
| Segunda importación | 0 registros creados; existentes omitidos (idempotente) |

### HTTP

| Petición | Código |
|---|---|
| Login desde el host | 200 |
| CSS | 200 |
| Ruta protegida sin sesión | 302 (redirección a login) |

### CMDB — `generate_cmdb --count 5000 --seed 2026` (SD-P03)

| Medida | Primera ejecución | Segunda ejecución |
|---|---|---|
| CI creados | 5000 | 0 |
| CI en el conjunto | 5000 | 5000 conservados |
| Relaciones nuevas | 510 | 0 |
| Vínculos CI–servicio nuevos | 100 | 0 |

Distribución por clasificación (5000 en total):

| Clasificación | CI |
|---|---|
| HW-ALM | 288 |
| HW-EST | 2912 |
| HW-IMP | 604 |
| HW-RED | 584 |
| HW-SRV | 612 |

### Service Desk demo — `seed_service_desk` (SD-X08)

| Medida | Resultado |
|---|---|
| Colas | 8 |
| Escenarios [DEMO] | 37 |
| Tickets totales | 39 |
| Estados distintos | 18 |
| Membresías de cola | 13 |
| Artículos FAQ | 5 |

| Proceso | Escenarios |
|---|---|
| ACCESOS | 5 |
| CAMBIOS | 5 |
| EVENTOS | 5 |
| INCIDENTES | 7 |
| NUEVOS_SERVICIOS | 5 |
| PROBLEMAS | 5 |
| SERVICIOS_TECNOLOGIA | 5 |

Segunda ejecución: 0 escenarios nuevos, 37 existentes, sin duplicación.

### SD-P16 — latencias medidas sobre 5,000 CI

Una medición por consulta, `django.test.Client` en el contenedor `web`.

| Consulta | Tiempo | HTTP |
|---|---|---|
| Página 1 | 116.2 ms | 200 |
| Página 40 | 49.0 ms | 200 |
| Página 100 | 39.0 ms | 200 |
| Búsqueda por código | 42.7 ms | 200 |
| Clasificación + estado | 50.3 ms | 200 |
| Responsable | 41.4 ms | 200 |
| Servicio | 23.7 ms | 200 |
| Grafo de impacto | 42.9 ms | 200 |

T no fija umbral de rendimiento; se registran los valores observados.

Código de salida del bloque: **EXIT=0**.

## 4. Suite automatizada completa — no concluida

Comando intentado:

~~~bash
python manage.py test tests --keepdb --parallel 1
~~~

Django descubrió **188 tests**. Durante la ejecución el equipo se congeló
por completo y hubo que reiniciarlo; no se obtuvo resultado final ni código
de salida.

**Suite automatizada completa iniciada pero no concluida por limitación de
recursos del equipo de evaluación/desarrollo.** No se afirma que los 188
tests pasaron ni que fallaron. Tampoco se ejecutaron `scripts/verify.sh` ni
`scripts/verify-persistence.sh` (SD-P18 / PP2-P12) en esta fase.

## 5. Consecuencias para la trazabilidad

- Verificados por evidencia real: SD-P02 y SD-P03 (operativos), SD-P16
  (latencias y HTTP 200), demo SD-X08 (colas/escenarios/estados), login y
  redirección anónima (parte de SD-P01).
- SD-P01 (resto), SD-P04–SD-P15, SD-P17 y regresiones PP2 tras el cambio de
  `Usuario.rol`: implementados en `tests/`, ejecución final no completada.
- SD-P07 (concurrencia) y SD-P18 (persistencia): implementados, sin resultado.

Estado detallado en [PRUEBAS](../PRUEBAS.md#estado-de-ejecución-cierre-sd) y
[MATRIZ](../MATRIZ_TRAZABILIDAD.md#cierre-service-desk-2026-10-29).
