#!/usr/bin/env bash
# Configuración pública y exclusivamente sintética; jamás source .env reales.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export QA_PROJECT="${QA_PROJECT:-catalogo-qa-$(date +%s)-$$}"
if [[ ! "$QA_PROJECT" =~ ^catalogo-qa-[0-9]+-[0-9]+$ ]]; then
  echo 'ERROR: el proyecto debe ser catalogo-qa-TIMESTAMP-PID.' >&2
  exit 2
fi
export DJANGO_SECRET_KEY=publica-sintetica-harness-no-usar-en-entrega
export DB_NAME=catalogo_qa DB_USER=catalogo_qa
export DB_PASSWORD=PublicaSinteticaQA2026
export DEMO_ADMIN_IDENTIFICADOR=admin.demo DEMO_CONSULTA_IDENTIFICADOR=consulta.demo
export DEMO_ADMIN_PASSWORD=PublicaAdminDemoQA2026
export DEMO_CONSULTA_PASSWORD=PublicaConsultaDemoQA2026
export DJANGO_DEBUG=false DJANGO_SECURE_COOKIES=false
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
export APP_PORT=18000

qa_compose() {
  docker compose --env-file .env.example -f compose.yaml -p "$QA_PROJECT" "$@"
}

qa_ready() {
  local qa_id qa_state qa_attempt
  for qa_attempt in {1..45}; do
    qa_id="$(qa_compose ps -q web)"
    qa_state="$(docker inspect --format '{{.State.Health.Status}}' "$qa_id" 2>/dev/null || true)"
    if [[ "$qa_state" == healthy ]]; then return 0; fi
    sleep 1
  done
  echo 'ERROR: web no alcanzó estado healthy en 45 segundos.' >&2
  return 1
}
