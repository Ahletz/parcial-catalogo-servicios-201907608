from django.http import FileResponse
from django.views.decorators.http import require_safe

from accounts.access import functional_access
from .servicios import adjunto_autorizado


@require_safe
@functional_access
def descargar_adjunto(request, identificador):
    """Sesión + autorización por ticket/visibilidad; nunca un enlace público."""
    adjunto = adjunto_autorizado(request.user, identificador)
    respuesta = FileResponse(
        adjunto.archivo.open("rb"), as_attachment=True,
        filename=adjunto.nombre_original, content_type=adjunto.tipo_mime,
    )
    respuesta["X-Content-Type-Options"] = "nosniff"
    respuesta["Content-Security-Policy"] = "default-src 'none'; sandbox"
    respuesta["Cache-Control"] = "private, no-store"
    return respuesta
