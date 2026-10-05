"""Solo datos sintéticos de pruebas; nunca SQLite ni el volumen de evaluación."""

import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403

test_name = os.environ.get("DB_TEST_NAME", "test_catalogo_modelos")
if not test_name.startswith("test_") or test_name == DATABASES["default"]["NAME"]:
    raise ImproperlyConfigured("La base de pruebas debe tener nombre test_ independiente.")
DATABASES["default"]["TEST"] = {"NAME": test_name}
