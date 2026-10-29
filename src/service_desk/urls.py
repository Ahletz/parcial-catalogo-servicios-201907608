from django.urls import path

from . import views

urlpatterns = [
    path("adjuntos/<uuid:identificador>/", views.descargar_adjunto, name="sd-adjunto"),
]
