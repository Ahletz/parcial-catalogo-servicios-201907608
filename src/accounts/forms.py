from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from config.forms import DomainForm, reference_field
from .models import Usuario


class LocalAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Identificador o contraseña incorrectos, o cuenta inactiva.",
        "inactive": "Esta cuenta está inactiva.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario o correo"


class UsuarioForm(DomainForm):
    nueva_password = forms.CharField(
        label="Nueva contraseña", required=False, strip=False,
        widget=forms.PasswordInput, help_text="Al editar, dejar vacía para conservarla.",
    )
    confirmar_password = forms.CharField(
        label="Confirmar contraseña", required=False, strip=False, widget=forms.PasswordInput,
    )

    class Meta:
        model = Usuario
        fields = ["identificador", "nombre", "rol", "is_active", "puesto"]
        labels = {"identificador": "Usuario o correo", "is_active": "Activo"}
        formfield_callback = reference_field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance._state.adding:
            self.instance.set_unusable_password()
            self.fields["nueva_password"].required = True
            self.fields["confirmar_password"].required = True

    def clean(self):
        data = super().clean()
        password = data.get("nueva_password")
        if password != data.get("confirmar_password"):
            self.add_error("confirmar_password", "Las contraseñas no coinciden.")
        if password:
            candidate = Usuario(
                identificador=data.get("identificador", ""), nombre=data.get("nombre", "")
            )
            validate_password(password, candidate)
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("nueva_password"):
            user.set_password(self.cleaned_data["nueva_password"])
        if commit:
            user.save()
        return user
