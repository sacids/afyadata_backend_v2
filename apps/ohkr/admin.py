from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Disease)
admin.site.register(ClinicalSignScore)
admin.site.register(Specie)



class ClinicalSignAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

admin.site.register(ClinicalSign, ClinicalSignAdmin)