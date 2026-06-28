"""urls.py — Routing utama: admin + API kobo_mce."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("kobo_mce.api_urls")),
]
