from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Specie)
admin.site.register(Disease)
admin.site.register(Response)


class ClinicalSignAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


admin.site.register(ClinicalSign, ClinicalSignAdmin)
admin.site.register(SpecieResponse)
admin.site.register(ClinicalSignScore)

@admin.register(ReactionAction)
class ReactionActionAdmin(admin.ModelAdmin):
    list_display = ('action_name', 'action_type', 'message')
    search_fields = ('action_name', 'message')

@admin.register(FormReaction)
class FormReactionAdmin(admin.ModelAdmin):
    list_display = ('rule_name', 'form_id', 'priority', 'is_active')
    list_filter = ('form_id', 'is_active')
    # This makes the Many-to-Many selection much easier
    filter_horizontal = ('actions',) 
    search_fields = ('rule_name', 'condition')
