"""Formularios compartidos; el dominio conserva la validación definitiva."""

from django import forms
from django.db.models import Q


class ReferenceChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        parent = getattr(obj, "parent_field", None)
        return f"{obj} · {getattr(obj, parent)}" if parent else str(obj)


class DomainForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field, forms.CharField) and name != "identificador":
                field.strip = False
            if not isinstance(field, forms.ModelChoiceField):
                continue
            model = field.queryset.model
            active, prefix = Q(), ""
            while model:
                state = getattr(model, "state_field", None)
                if state:
                    active &= Q(**{prefix + state: True})
                parent = getattr(model, "parent_field", None)
                if not parent:
                    break
                prefix += parent + "__"
                model = model._meta.get_field(parent).related_model
            current = getattr(self.instance, name + "_id", None)
            if current:
                active |= Q(pk=current)
            field.queryset = field.queryset.filter(active)


def reference_field(model_field, **kwargs):
    if model_field.many_to_one:
        kwargs["form_class"] = ReferenceChoice
        kwargs["error_messages"] = {
            "invalid_choice": "Selecciona una referencia existente y activa."
        }
    return model_field.formfield(**kwargs)


def add_domain_errors(form, error):
    errors = error.message_dict if hasattr(error, "message_dict") else {None: error.messages}
    for name, messages in errors.items():
        for message in messages:
            form.add_error(name if name in form.fields else None, message)
