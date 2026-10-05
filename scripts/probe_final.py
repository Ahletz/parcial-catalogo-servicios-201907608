"""Importación/demo repetidas y HTTP de la web final, solo datos sintéticos."""
import http.cookiejar
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

import django

if os.environ.get("DB_NAME") != "catalogo_qa" or os.environ.get("DB_USER") != "catalogo_qa":
    raise SystemExit("El probe final solo admite catalogo_qa.")
django.setup()
from accounts.models import Usuario
from catalog.models import ServicioNivel1, ServicioNivel2
from organization.models import Empresa
from probe_funcional import CSRFToken, require

def command(*args):
    result = subprocess.run([sys.executable, "manage.py", *args], capture_output=True,
                            text=True, check=False)
    require(result.returncode == 0, f"Comando {args[0]} falló con código {result.returncode}.")
    # import_catalog antepone una línea de estado al resumen JSON aprobado.
    return json.loads(result.stdout[result.stdout.index("{"):])

first = command("import_catalog", "--file", "/app/data/CatalogoServicios.xlsx")
second = command("import_catalog", "--file", "/app/data/CatalogoServicios.xlsx")
demo_first, demo_second = command("seed_demo"), command("seed_demo")
require(ServicioNivel1.objects.count() == 12 and ServicioNivel2.objects.count() == 46,
        "Conteo de importación incorrecto.")
require(second["totales"]["creados"] == 0 and second["totales"]["actualizados"] == 0,
        "Reimportación no idempotente.")
require(demo_first["usuarios_creados"] == 2 and demo_first["asignaciones_validas"] >= 3
        and demo_second["usuarios_creados"] == 0 and demo_second["asignaciones_creadas"] == 0,
        "Demo no reproducible.")
assigned = list(ServicioNivel2.objects.filter(usuario_responsable__isnull=False))
require(len(assigned) >= 3 and all(item.usuario_responsable.seccion.pk == item.seccion_responsable_id
                                for item in assigned), "Responsables inválidos.")

jar = http.cookiejar.CookieJar()
browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def request(path, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request("http://web:8000" + path, data=body, headers={"Host": "localhost:8000"})
    try:
        response = browser.open(req, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.geturl(), response.read().decode()

_, target, _ = request("/")
require("/login/" in target, "Anónimo no redirigido.")
require(request("/static/app.css")[0] == 200, "CSS final inaccesible.")
for identifier, variable, role in (
    ("admin.demo", "DEMO_ADMIN_PASSWORD", Usuario.Rol.ADMINISTRADOR),
    ("consulta.demo", "DEMO_CONSULTA_PASSWORD", Usuario.Rol.CONSULTA),
):
    _, _, login = request("/login/")
    status, destination, home = request("/login/", {"username": identifier,
        "password": os.environ[variable], "csrfmiddlewaretoken": CSRFToken(login).value})
    require(status == 200 and urllib.parse.urlsplit(destination).path == "/", "Login demo falló.")
    for path in ("/organizacion/", "/datos/usuarios/", "/datos/servicios/", "/clasificaciones/",
                 f"/servicios/{assigned[0].pk}/"):
        require(request(path)[0] == 200, f"Página funcional falló: {path}")
    if role == Usuario.Rol.ADMINISTRADOR:
        _, _, form = request("/datos/empresas/nuevo/")
        require(request("/datos/empresas/nuevo/", {"codigo": "HTTP-FINAL", "nombre": "Empresa HTTP final",
            "estado": "on", "csrfmiddlewaretoken": CSRFToken(form).value})[0] == 200, "Alta admin falló.")
        require(Empresa.objects.filter(codigo="HTTP-FINAL").exists(), "Alta HTTP no persistida.")
    else:
        require(request("/datos/empresas/nuevo/", {"codigo": "PROHIBIDO-FINAL", "nombre": "Prohibido",
            "estado": "on", "csrfmiddlewaretoken": CSRFToken(home).value})[0] == 403, "CONSULTA escribió.")
        require(not Empresa.objects.filter(codigo="PROHIBIDO-FINAL").exists(), "Dato prohibido persistido.")
    _, _, home = request("/")
    old_cookie = next(cookie for cookie in jar if cookie.name == "sessionid")
    request("/logout/", {"csrfmiddlewaretoken": CSRFToken(home).value})
    jar.set_cookie(old_cookie)
    require("/login/" in request("/")[1], "Cookie tras logout reutilizable.")
    jar.clear()
print(json.dumps({"importacion_primera": first, "importacion_segunda": second,
                  "demo_primera": demo_first, "demo_segunda": demo_second,
                  "http": "ambos_roles_lectura_escritura_logout_css_OK", "n1": 12, "n2": 46},
                 ensure_ascii=False, indent=2))
