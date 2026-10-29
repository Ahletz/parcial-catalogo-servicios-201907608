from django.urls import path

from . import views

urlpatterns = [
    path("", views.ci_lista, name="cmdb-lista"),
    path("<str:codigo>/", views.ci_detalle, name="cmdb-ci"),
    path("<str:codigo>/grafo/", views.ci_grafo, name="cmdb-grafo"),
]
