"""CLI demo repetida y HTTP real sobre una base sintética nueva conservada."""

import http.cookiejar
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def command(*args):
    result = subprocess.run([sys.executable, "manage.py", *args], capture_output=True,
                            text=True, check=False)
    require(result.returncode == 0, f"Comando {args[0]} falló: {result.stderr}")
    return result


class CSRFToken(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.value = None
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("name") == "csrfmiddlewaretoken":
            self.value = attrs.get("value")


def main():
    require(os.environ.get("DB_NAME") == "catalogo_modelos"
            and os.environ.get("DB_HOST") == "db" and os.environ.get("DB_USER") == "modelos",
            "La demostración solo admite el Compose interno autorizado.")
    database = "test_funcional_evidencia_" + uuid4().hex
    with psycopg.connect(dbname="postgres", host="db", user="modelos", autocommit=True) as admin:
        with admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    os.environ["DB_NAME"] = database
    # Datos sintéticos efímeros: no se leen credenciales reales ni se imprimen.
    password = "verificacion-sintetica-" + uuid4().hex
    os.environ.update({
        "DEMO_ADMIN_IDENTIFICADOR": "admin.demo", "DEMO_ADMIN_PASSWORD": password,
        "DEMO_CONSULTA_IDENTIFICADOR": "consulta.demo", "DEMO_CONSULTA_PASSWORD": password,
    })
    source = Path("/app/data/CatalogoServicios.xlsx")
    before = sha256(source.read_bytes()).hexdigest()
    migrate = command("migrate", "--noinput")
    imported = command("import_catalog", "--file", str(source))
    first = command("seed_demo")
    second = command("seed_demo")
    reports = [json.loads(first.stdout), json.loads(second.stdout)]
    require(reports[0]["asignaciones_creadas"] == 3 and reports[0]["usuarios_creados"] == 2,
            "Primera carga demo incompleta.")
    require(reports[1]["asignaciones_creadas"] == 0 and reports[1]["usuarios_creados"] == 0
            and reports[1]["estructura_creada"] == 0, "Carga demo no idempotente.")
    import django
    django.setup()
    from catalog.models import ServicioNivel1, ServicioNivel2

    require(ServicioNivel1.objects.count() == 12 and ServicioNivel2.objects.count() == 46,
            "La demo alteró cardinalidades del original.")
    assigned = list(ServicioNivel2.objects.filter(usuario_responsable__isnull=False))
    require(len(assigned) == 3 and all(
        obj.usuario_responsable.seccion.pk == obj.seccion_responsable_id for obj in assigned
    ), "Asignaciones inconsistentes.")

    server = subprocess.Popen([
        "gunicorn", "config.wsgi:application", "--bind", "127.0.0.1:8088",
        "--workers", "1", "--access-logfile", "/dev/null", "--error-logfile", "/dev/null",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    jar = http.cookiejar.CookieJar()
    browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    base = "http://localhost:8088"

    def request(path, data=None):
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        try:
            response = browser.open(base + path, data=body, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, response.geturl(), response.read().decode()

    results = {}
    try:
        deadline = time.monotonic() + 15
        while True:
            try:
                require(server.poll() is None, "Gunicorn terminó antes de iniciar.")
                status, _, login = request("/login/")
                if status == 200:
                    break
            except urllib.error.URLError:
                pass
            require(time.monotonic() < deadline, "Servidor HTTP no disponible.")
            time.sleep(0.1)
        require("Usuario o correo" in login, "Login no renderizado.")
        status, _, css = request("/static/app.css")
        require(status == 200 and "font-family" in css, "CSS local no disponible.")
        results["css_local"] = status
        _, destination, _ = request("/")
        require("/login/" in destination, "Ruta anónima desprotegida.")
        results["anonimo_redirigido_login"] = True
        _, _, login = request("/login/")
        status, destination, home = request("/login/", {
            "username": "admin.demo", "password": password,
            "csrfmiddlewaretoken": CSRFToken(login).value,
        })
        require(status == 200 and urllib.parse.urlsplit(destination).path == "/"
                and "Administrador" in home, "Login administrador no funciona.")
        results["login_admin_destino"] = "/"
        for path in ("/organizacion/", "/datos/usuarios/", "/datos/servicios/",
                     "/clasificaciones/", f"/servicios/{assigned[0].pk}/"):
            status, _, _ = request(path)
            require(status == 200, f"Página funcional no disponible: {path}")
        results["paginas_funcionales"] = 5
        require(request("/datos/empresas/nuevo/", {"codigo": "SIN-CSRF"})[0] == 403,
                "Escritura sin CSRF aceptada.")
        results["escritura_sin_csrf"] = 403
        _, _, form = request("/datos/empresas/nuevo/")
        status, _, _ = request("/datos/empresas/nuevo/", {
            "codigo": "HTTP-DEMO", "nombre": "Empresa HTTP sintética", "estado": "on",
            "csrfmiddlewaretoken": CSRFToken(form).value,
        })
        require(status == 200, "Alta administrador no funciona.")
        from organization.models import Empresa
        require(Empresa.objects.filter(codigo="HTTP-DEMO").exists(), "Alta HTTP no persistida.")
        results["alta_admin_persistida"] = True
        _, _, home = request("/")
        previous_cookie = next(cookie for cookie in jar if cookie.name == "sessionid")
        request("/logout/", {"csrfmiddlewaretoken": CSRFToken(home).value})
        jar.set_cookie(previous_cookie)
        require("/login/" in request("/")[1], "Cookie anterior reutilizable después de logout.")
        results["cookie_tras_logout_rechazada"] = True
        _, _, login = request("/login/")
        status, destination, home = request("/login/", {
            "username": "consulta.demo", "password": password,
            "csrfmiddlewaretoken": CSRFToken(login).value,
        })
        require(status == 200 and urllib.parse.urlsplit(destination).path == "/"
                and "Consulta" in home, "Login consulta no funciona.")
        require(request("/datos/servicios/")[0] == 200, "Consulta no puede leer.")
        require(request("/datos/empresas/nuevo/", {
            "codigo": "NO-PERMITIDO", "nombre": "No permitido", "estado": "on",
            "csrfmiddlewaretoken": CSRFToken(home).value,
        })[0] == 403, "Consulta consiguió escribir.")
        require(not Empresa.objects.filter(codigo="NO-PERMITIDO").exists(), "Escritura prohibida persistida.")
        results["consulta_lectura"] = 200
        results["consulta_escritura"] = 403
    finally:
        server.terminate()
        server.wait(timeout=10)
    after = sha256(source.read_bytes()).hexdigest()
    require(before == after, "Excel modificado.")
    print(json.dumps({
        "base_pruebas_conservada": database,
        "codigos_cli": [migrate.returncode, imported.returncode, first.returncode, second.returncode],
        "primera_demo": reports[0], "segunda_demo": reports[1],
        "n1": 12, "n2": 46, "asignaciones_validas": 3, "http_real": results,
        "sha256_antes": before, "sha256_despues": after,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
