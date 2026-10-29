from django.urls import path

from . import views

urlpatterns = [
    path("", views.portal, name="sd-portal"),
    path("tickets/", views.ticket_lista, name="sd-tickets"),
    path("tickets/nuevo/", views.ticket_nuevo, name="sd-ticket-nuevo"),
    path("tickets/<str:numero>/", views.ticket_detalle, name="sd-ticket"),
    path("tickets/<str:numero>/grafo/", views.grafo_ticket, name="sd-ticket-grafo"),
    path("colas/", views.colas, name="sd-colas"),
    path("colas/<str:codigo>/", views.cola_detalle, name="sd-cola"),
    path("faq/", views.faq, name="sd-faq"),
    path("faq/<int:pk>/", views.faq_detalle, name="sd-faq-detalle"),
    path("tablero/", views.tablero, name="sd-tablero"),
    path("adjuntos/<uuid:identificador>/", views.descargar_adjunto, name="sd-adjunto"),
]
