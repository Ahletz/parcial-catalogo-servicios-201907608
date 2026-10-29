#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/verify-common.sh"
qa_compose up --build -d
qa_ready
qa_before="$(qa_compose exec -T web python /app/scripts/persistence_record.py crear)"
qa_db_before="$(qa_compose ps -q db)"
qa_web_before="$(qa_compose ps -q web)"
qa_volume_before="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$qa_db_before")"
qa_compose stop
qa_compose up -d --force-recreate db init web
qa_ready
qa_after="$(qa_compose exec -T web python /app/scripts/persistence_record.py comprobar)"
qa_db_after="$(qa_compose ps -q db)"
qa_web_after="$(qa_compose ps -q web)"
qa_volume_after="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$qa_db_after")"
[[ "$qa_before" == "$qa_after" && "$qa_db_before" != "$qa_db_after" && "$qa_web_before" != "$qa_web_after" && -n "$qa_volume_before" && "$qa_volume_before" == "$qa_volume_after" ]]
printf '%s\n' "$qa_before" "$qa_after"
printf 'SD-P18/PP2-P12 APROBADA: db/web recreados, volumen %s conservado, dato idéntico.\n' "$qa_volume_after"
