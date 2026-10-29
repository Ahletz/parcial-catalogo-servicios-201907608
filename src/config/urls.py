from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from accounts.forms import LocalAuthenticationForm
from . import web

urlpatterns = [
    path("login/", LoginView.as_view(
        template_name="registration/login.html", authentication_form=LocalAuthenticationForm,
        redirect_authenticated_user=True,
    ), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", web.home, name="home"),
    path("organizacion/", web.organization, name="organization"),
    path("clasificaciones/", web.classifications, name="classifications"),
    path("datos/<slug:entity>/", web.entity_list, name="entity-list"),
    path("datos/<slug:entity>/nuevo/", web.entity_form, name="entity-create"),
    path("datos/<slug:entity>/<int:pk>/editar/", web.entity_form, name="entity-edit"),
    path("datos/<slug:entity>/<int:pk>/desactivar/", web.deactivate, name="entity-deactivate"),
    path("servicios/<int:pk>/", web.service_detail, name="service-detail"),
    path("service-desk/", include("service_desk.urls")),
]
