from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from lib.views import logout_view

from blogs_api.swagger import SchemaView

# type:ignore
urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    path("accounts/logout", logout_view, name="logout"),
    # Version 1 API
    path("api/v1/", include("core.urls")),
    # Docs
    path(
        "api-docs/",
        SchemaView.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        SchemaView.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    path(
        "favicon.ico",
        RedirectView.as_view(url="https://assets.website-files.com/631c1d6a8a1dd41a860f11ec/631c1d6a8a1dd478dd0f1222_favicon.png"),
    ),

]

admin.site.site_header = "Blog API"
admin.site.site_title = "Blog API"
admin.site.index_title = "Blog API"
