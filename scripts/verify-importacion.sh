#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."

docker compose -f compose.modelos.yaml build modelos
docker compose -f compose.modelos.yaml up -d db
docker compose -f compose.modelos.yaml run --rm modelos python /app/scripts/check_sources.py
docker compose -f compose.modelos.yaml run --rm modelos python -m pip check
docker compose -f compose.modelos.yaml run --rm modelos python manage.py check
docker compose -f compose.modelos.yaml run --rm modelos python manage.py migrate --noinput
docker compose -f compose.modelos.yaml run --rm modelos python manage.py makemigrations --check --dry-run
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_import_parser tests.test_import_persistence --keepdb --verbosity 2
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_import_acceptance.OfficialImportAcceptanceTests.test_P06_importar_original --keepdb --verbosity 2
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_import_acceptance.OfficialImportAcceptanceTests.test_P07_repetir_importacion --keepdb --verbosity 2
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_import_acceptance.OfficialImportAcceptanceTests.test_P08_se12_y_ausencias --keepdb --verbosity 2
docker compose -f compose.modelos.yaml run --rm modelos python /app/scripts/probe_importacion.py
docker compose -f compose.modelos.yaml run --rm modelos python /app/scripts/check_sources.py
