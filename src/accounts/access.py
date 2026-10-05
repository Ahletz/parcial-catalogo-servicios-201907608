from functools import wraps

from django.contrib.auth import SESSION_KEY, logout
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Usuario


def functional_access(view=None, *, write=False):
    def decorate(function):
        @wraps(function)
        def guarded(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or not user.is_active:
                if user.is_authenticated or SESSION_KEY in request.session:
                    logout(request)
                return redirect_to_login(request.get_full_path())
            if user.rol not in Usuario.Rol.values:
                raise PermissionDenied("Rol sin acceso funcional.")
            if write and user.rol != Usuario.Rol.ADMINISTRADOR:
                raise PermissionDenied("Solo el administrador puede modificar datos.")
            return function(request, *args, **kwargs)
        return guarded
    return decorate(view) if view else decorate
