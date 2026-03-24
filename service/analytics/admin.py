from django.contrib import admin

from .models import PartyStatistics


@admin.register(PartyStatistics)
class PartyStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "party_name",
        "year",
        "semester",
        "drinks_count",
        "shots_count",
        "flirts_count",
        "kisses_count",
        "success_rate",
    )

    list_filter = ("user", "party_name", "year", "semester")

    search_fields = ("user__username", "party_name")

    readonly_fields = ("success_rate", "created_at", "updated_at")

    fieldsets = (
        ("Identificação", {"fields": ("user", "party_name", "year", "semester", "is_present")}),
        ("Métricas de Consumo", {"fields": ("drinks_count", "shots_count")}),
        ("Social & Performance", {"fields": ("flirts_count", "kisses_count", "success_rate")}),
        ("Tempo de Festa", {"fields": ("arrival_time", "leave_time")}),
        (
            "Metadados (Sistema)",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
