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
docker compose -f compose.modelos.yaml run --rm modelos python manage.py test tests --keepdb --verbosity 2
