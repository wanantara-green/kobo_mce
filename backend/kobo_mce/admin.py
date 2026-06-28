"""admin.py — Registrasi model di Django admin untuk audit manual."""
from django.contrib import admin
from .models import ExpertResponse, PairwiseValue

class PairwiseInline(admin.TabularInline):
    model = PairwiseValue
    extra = 0

@admin.register(ExpertResponse)
class ExpertResponseAdmin(admin.ModelAdmin):
    list_display = ("expert_id", "nama", "tipologi", "is_valid", "submitted_at")
    list_filter = ("tipologi", "is_valid")
    search_fields = ("expert_id", "nama", "instansi")
    inlines = [PairwiseInline]
