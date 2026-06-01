from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(ReferenceData)
class ReferenceDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'rd_type', 'code')
    search_fields = ('name', 'rd_type')
    list_filter = ('rd_type',)

admin.site.register(OHKRScore)
admin.site.register(OHKRResponse)

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
