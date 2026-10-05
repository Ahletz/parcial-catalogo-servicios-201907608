#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."

# Solo configuración pública de ejemplo; jamás cargar .env reales al verificar.
docker compose --env-file .env.example -f compose.modelos.yaml build modelos
docker compose --env-file .env.example -f compose.modelos.yaml up -d db
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python /app/scripts/check_sources.py
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python -m pip check
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python manage.py check
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python manage.py migrate --noinput
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python manage.py makemigrations --check --dry-run
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python manage.py test tests.test_web_acceptance tests.test_web_security tests.test_web_maintenance tests.test_seed_demo --keepdb --verbosity 2
# Única invocación de suite completa del cierre: incluye las 126 regresiones.
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python manage.py test tests --keepdb --verbosity 2
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python /app/scripts/probe_funcional.py
docker compose --env-file .env.example -f compose.modelos.yaml run --rm modelos python /app/scripts/check_sources.py
