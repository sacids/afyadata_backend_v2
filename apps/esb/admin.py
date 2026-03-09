from django.contrib import admin
from .models import *

# Register your models here.
class FormPayloadFieldMapInline(admin.TabularInline):
    model = FormPayloadFieldMap
    ordering = ("id",)
    extra = 0

class FormValueMappingInline(admin.TabularInline):
    model = FormValueMapping
    ordering = ("id",)
    extra = 0


@admin.register(FormPayloadConfig)
class FormPayloadConfigAdmin(admin.ModelAdmin):
    list_display = ["form", "endpoint", "method", "is_active"]
    ordering = ("form",)
    inlines = [FormPayloadFieldMapInline, FormValueMappingInline]
    list_per_page = 25