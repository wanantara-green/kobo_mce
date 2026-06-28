"""api_urls.py — Routing endpoint API kobo_mce."""
from django.urls import path
from . import views

urlpatterns = [
    path("submit/", views.submit_response, name="submit"),
    path("experts/", views.list_experts, name="experts"),
    path("weights/", views.compute_weights, name="weights"),
    path("validate/", views.validate_only, name="validate"),
    path("narrative/", views.narrative, name="narrative"),
]
