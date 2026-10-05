#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
docker compose --env-file .env.example -f compose.modelos.yaml build modelos
docker compose --env-file .env.example -f compose.modelos.yaml --profile funcional up --build -d web
# HTTP anónimo desde el anfitrión Docker; no imprime HTML, cookies ni tokens.
docker run --rm --interactive --network host catalogo-modelos-201907608-modelos python - <<'PY'
import json
import time
import urllib.error
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, target):
        return None

browser = urllib.request.build_opener(NoRedirect)
base = "http://127.0.0.1:8000"
deadline = time.monotonic() + 30
while True:
    try:
        with browser.open(base + "/login/", timeout=2) as response:
            assert response.status == 200, "Login local no disponible."
            break
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        if time.monotonic() >= deadline:
            raise RuntimeError("Puerto local 8000 no disponible.")
        time.sleep(0.2)
with browser.open(base + "/static/app.css", timeout=5) as response:
    assert response.status == 200, "CSS local no disponible."
try:
    browser.open(base + "/", timeout=5)
except urllib.error.HTTPError as error:
    assert error.code == 302 and error.headers["Location"].startswith("/login/"), "Ruta anónima desprotegida."
else:
    raise AssertionError("Ruta anónima desprotegida.")
print(json.dumps({"login": 200, "css": 200, "anonimo": 302}))
PY
