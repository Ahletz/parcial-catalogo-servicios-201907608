"""HTTP desde el anfitrión Docker; no imprime respuestas ni cookies."""
import json
import os
import urllib.error
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, target):
        return None

browser = urllib.request.build_opener(NoRedirect)
base = "http://127.0.0.1:" + os.environ.get("APP_PORT", "18000")
for path in ("/login/", "/static/app.css"):
    with browser.open(base + path, timeout=5) as response:
        assert response.status == 200
try:
    browser.open(base + "/", timeout=5)
except urllib.error.HTTPError as error:
    assert error.code == 302 and error.headers["Location"].startswith("/login/")
else:
    raise AssertionError("Ruta anónima desprotegida.")
print(json.dumps({"host_login": 200, "host_css": 200, "host_anonimo": 302}))
