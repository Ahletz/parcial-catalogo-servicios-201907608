"""Almacenamiento privado y validación de adjuntos (sin importar modelos)."""

import hashlib
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.utils.text import get_valid_filename

# Extensiones conocidas: tipo MIME servido y firma de contenido exigida.
FORMATOS = {
    "pdf": ("application/pdf", (b"%PDF-",)),
    "png": ("image/png", (b"\x89PNG\r\n\x1a\n",)),
    "jpg": ("image/jpeg", (b"\xff\xd8\xff",)),
    "jpeg": ("image/jpeg", (b"\xff\xd8\xff",)),
    "txt": ("text/plain", None),
}
MIME_GENERICO = "application/octet-stream"


def almacen_adjuntos():
    """Directorio fuera de static/media: solo la vista autorizada lo sirve."""
    return FileSystemStorage(location=settings.SD_ADJUNTOS_DIR, base_url=None)


def ruta_adjunto(instancia, _nombre_usuario):
    # Nunca se usa el nombre aportado por el usuario para la ruta física.
    return f"{instancia.ticket_id}/{uuid.uuid4().hex}.{instancia.extension}"


def nombre_seguro(nombre):
    base = os.path.basename((nombre or "").replace("\\", "/")).strip()
    try:
        limpio = get_valid_filename(base)
    except Exception:  # get_valid_filename rechaza nombres vacíos o «..».
        limpio = ""
    raiz, ext = os.path.splitext(limpio)
    return (raiz[:150] or "adjunto") + ext.lower()[:9]


def validar_archivo(archivo):
    """Valida tamaño, extensión, MIME declarado y firma; devuelve metadatos."""
    maximo = settings.SD_ADJUNTO_MAX_BYTES
    if archivo.size is None or archivo.size <= 0:
        raise ValidationError("El adjunto está vacío.")
    if archivo.size > maximo:
        raise ValidationError(f"El adjunto supera el máximo de {maximo} bytes.")
    nombre = nombre_seguro(archivo.name)
    extension = os.path.splitext(nombre)[1].lstrip(".")
    if extension not in settings.SD_ADJUNTO_EXTENSIONES or extension not in FORMATOS:
        raise ValidationError("Extensión de adjunto no permitida.")
    mime, firmas = FORMATOS[extension]
    declarado = (getattr(archivo, "content_type", "") or "").split(";")[0].strip().lower()
    if declarado and declarado not in {mime, MIME_GENERICO}:
        raise ValidationError("El tipo MIME declarado no coincide con la extensión.")
    digest = hashlib.sha256()
    archivo.seek(0)
    inicio = archivo.read(16)
    archivo.seek(0)
    if firmas and not any(inicio.startswith(f) for f in firmas):
        raise ValidationError("El contenido no corresponde al tipo de archivo declarado.")
    contenido_texto = bytearray() if firmas is None else None
    for bloque in archivo.chunks():
        digest.update(bloque)
        if contenido_texto is not None:
            contenido_texto.extend(bloque)
    archivo.seek(0)
    if contenido_texto is not None:
        if b"\x00" in contenido_texto:
            raise ValidationError("Un texto plano no puede contener bytes nulos.")
        try:
            contenido_texto.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValidationError("El texto debe estar codificado en UTF-8.") from error
    return {
        "nombre_original": nombre, "extension": extension, "tipo_mime": mime,
        "tamano": archivo.size, "sha256": digest.hexdigest(),
    }
