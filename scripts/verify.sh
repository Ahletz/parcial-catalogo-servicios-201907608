#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/verify-common.sh"
qa_started=$SECONDS
qa_finish() {
  local qa_code=$?
  trap - EXIT
  qa_compose stop >/dev/null 2>&1 || true
  printf 'HARNESS FINAL: codigo=%s duracion=%ss proyecto=%s volumen_conservado=%s_datos_postgres\n' "$qa_code" "$((SECONDS-qa_started))" "$QA_PROJECT" "$QA_PROJECT"
  exit "$qa_code"
}
trap qa_finish EXIT
qa_compose config --quiet
qa_compose up --build -d
qa_ready
qa_compose exec -T web python /app/scripts/check_sources.py
qa_compose exec -T web python -m pip check
qa_compose exec -T web python manage.py check
qa_compose exec -T web python manage.py makemigrations --check --dry-run
qa_compose run --rm runner python /app/scripts/probe_final.py
docker run --rm --network host -e APP_PORT="$APP_PORT" catalogo-servicios:local python /app/scripts/probe_host.py
# Datos SD: 5,000 CI (dos veces, misma semilla) + demo (dos veces); SD-P03/P16 con tiempos.
qa_compose exec -T web python /app/scripts/probe_service_desk.py
# ÚNICA invocación completa: PP2 (P01–P11 y regresiones) + SD-P01–SD-P17.
qa_compose run --rm runner python manage.py test tests --keepdb --verbosity 2
# SD-P18 / PP2-P12: recrear db/web y comprobar catálogo, CMDB, tickets e historial.
bash scripts/verify-persistence.sh
qa_compose exec -T web python /app/scripts/check_sources.py
echo 'PP2 P01-P12 y SD-P01-P18 APROBADAS. VERIFICACION FINAL OK.'
