"""Configuración PostgreSQL; no lee archivos .env ni incluye secretos reales."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def required_env(name):
    value = os.environ.get(name)
    if not value or value == "CONFIGURAR_LOCALMENTE":
        raise ImproperlyConfigured(f"Configura la variable {name} localmente.")
    return value


def env_bool(name, default=False):
    value = os.environ.get(name, str(default)).lower()
    if value not in {"true", "false", "1", "0"}:
        raise ImproperlyConfigured(f"{name} debe ser true/false o 1/0.")
    return value in {"true", "1"}


SECRET_KEY = required_env("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG")
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
).split(",")
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "organization",
    "accounts",
    "catalog",
    "imports",
    "cmdb",
    "processes",
    "service_desk",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": required_env("DB_NAME"),
    "USER": required_env("DB_USER"),
    "PASSWORD": os.environ.get("DB_PASSWORD", ""),
    "HOST": os.environ.get("DB_HOST", "db"),
    "PORT": os.environ.get("DB_PORT", "5432"),
    "CONN_MAX_AGE": 0,
}}
AUTH_USER_MODEL = "accounts.Usuario"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
SESSION_ENGINE = "django.contrib.sessions.backends.db"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_AGE = 7200
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES")
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Guatemala"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR.parent / "staticfiles"
# Adjuntos Service Desk: directorio privado, nunca servido como estático/media.
SD_ADJUNTOS_DIR = Path(
    os.environ.get("SD_ADJUNTOS_DIR", BASE_DIR.parent / "privado" / "adjuntos")
)
SD_ADJUNTO_MAX_BYTES = int(os.environ.get("SD_ADJUNTO_MAX_BYTES", 10 * 1024 * 1024))
SD_ADJUNTO_EXTENSIONES = frozenset(
    os.environ.get("SD_ADJUNTO_EXTENSIONES", "pdf,png,jpg,jpeg,txt").lower().split(",")
)
FILE_UPLOAD_PERMISSIONS = 0o640
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
