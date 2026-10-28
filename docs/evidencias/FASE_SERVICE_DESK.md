# Evidencia — integración CMDB y núcleo Service Desk

Fecha: 2026-10-29, America/Guatemala. Prompt [SD-PE03](../prompts/SD_P03_SERVICE_DESK.md).
Repositorio real: `/home/alex/Escritorio/parcial-catalogo-servicios-201907608`,
rama `main`, base 396aa81, tres archivos sin seguimiento del usuario intactos.

## 1. Escritura y entorno

- `.claude_write_test` creado y eliminado: escritura correcta.
- `docker ps`: disponible (sin contenedores en ejecución).
- Host sin Django instalado; los comandos Django se ejecutaron con la imagen
  local `catalogo-servicios:local` montando `src/` y un PostgreSQL 17
  **efímero** (`postgres:17-bookworm`, contenedor `sd-verif-db` sin volumen,
  red `--internal` `sd-verif-net`). El volumen de evaluación `datos_postgres`
  no se tocó. Configuración sintética, sin leer `.env`.

## 2. Integración CMDB

`git bundle verify` correcto (requiere 396aa81, contiene `main` 35403e6).
`git fetch <bundle> main` + `git merge --ff-only FETCH_HEAD`: fast-forward
396aa81→35403e6 con los commits originales 2fb2521 y 35403e6, sin commit nuevo.
El parche no se aplicó (mecanismo alternativo, no ambos).

## 3. Controles de CMDB (antes de Service Desk)

| Comando | Código | Salida |
|---|---|---|
| `manage.py check` | 0 | System check identified no issues (0 silenced). |
| `manage.py makemigrations --check --dry-run` | 0 | No changes detected |
| `manage.py migrate --noinput` | 0 | … `cmdb.0001_initial... OK` |

## 4. Controles finales (con Service Desk)

| Comando | Código | Salida |
|---|---|---|
| `manage.py makemigrations accounts service_desk processes` | 0 | accounts 0002 (renombrada `0002_rol_operativo`), service_desk 0001, processes 0001/0002 |
| `manage.py check` | 0 | System check identified no issues (0 silenced). |
| `manage.py makemigrations --check --dry-run` | 0 | No changes detected |
| `manage.py migrate --noinput` | 0 | `accounts.0002_rol_operativo`, `service_desk.0001_initial`, `processes.0001_initial`, `processes.0002_initial` OK |

Tras ajustes posteriores sin cambios de esquema se repitieron `check` y
`makemigrations --check --dry-run`: ambos 0.

## 5. Lo que no se ejecutó

Ninguna prueba Django (PP2 ni SD), ni SD-P01–P18, ni `scripts/verify.sh`, ni
prueba de concurrencia P07, ni carga de datos, `seed_demo` o importaciones.
Las reglas de procesos, permisos, adjuntos y concurrencia están implementadas
pero **no verificadas funcionalmente**. Las regresiones PP2 que tocan
`Usuario.rol` (nuevo valor OPERATIVO) deben ejecutarse en la próxima fase.

## 6. Correcciones durante la fase

- Reproducción manual de `src/cmdb` iniciada por respuesta del usuario cuando
  los artefactos parecían ausentes; descartada sin commit al localizarlos.
- Revisión estática: nombre de archivo subido sanitizado antes de validar el
  FileField; líneas largas; guarda que impide retirar la capacidad atender de
  quien tiene tickets abiertos asignados. No son ciclos de Loop Engineering:
  no hubo ejecución fallida previa ni repetición de un control funcional.
