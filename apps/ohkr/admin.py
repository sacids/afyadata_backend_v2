from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Specie)
admin.site.register(Disease)
admin.site.register(ClinicalResponse)


class ClinicalSignAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


admin.site.register(ClinicalSign, ClinicalSignAdmin)
admin.site.register(SpecieResponse)
admin.site.register(ClinicalSignScore)


from django.contrib import admin
from .models import FirstAidAction, FirstAidRule


@admin.register(FirstAidAction)
class FirstAidActionAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "priority")
    list_filter = ("category",)
    search_fields = ("title", "description", "code")


@admin.register(FirstAidRule)
class FirstAidRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "updated_at")
    # filter_horizontal creates a nice UI for selecting multiple M2M items
    filter_horizontal = ("species", "clinical_signs", "actions")
    list_filter = ("active", "species")
    search_fields = ("name",)

    fieldsets = (
        ("Basic Info", {"fields": ("name", "active")}),
        (
            "Conditions (Logic)",
            {
                "description": "The rule triggers if ANY of these signs match the selection.",
                "fields": (
                    "species",
                    "clinical_signs",
                    "min_age_months",
                    "max_age_months",
                ),
            },
        ),
        (
            "Responses",
            {
                "description": "These actions will be bundled together for the collector.",
                "fields": ("actions",),
            },
        ),
    )
