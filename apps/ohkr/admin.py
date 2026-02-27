from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Specie)
admin.site.register(Disease)
admin.site.register(Response)


class ClinicalSignAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

admin.site.register(ClinicalSign, ClinicalSignAdmin)
admin.site.register(SpecieResponse)
admin.site.register(ClinicalSignScore)