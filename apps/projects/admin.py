from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['title']
    ordering = ("title",)


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    ordering = ("id", )
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'access', 'auto_join', "active", "created_at"]
    ordering = ("id",)
    readonly_fields = ('created_at', 'updated_at')
    inlines  = [ProjectMemberInline]
    filter_horizontal = ["tags"]
    list_per_page = 25


@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_title', 'version', 'code', 'sort_order', 'created_at', 'created_by', 'updated_at', 'updated_by')
    list_filter = ('created_at', 'updated_at', 'created_by', 'updated_by')
    search_fields = ('title', 'short_title', 'version', 'code', 'description')
    ordering = ('sort_order', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('project','title', 'short_title', 'version', 'code', 'sort_order')
        }),
        ('Form Definition Details', {
            'fields': ('xlsform', 'form_defn', 'description', 'children')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FormData)
class FormDataAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'form', 'title', 'created_at', 'submitted_at', 'created_by', 'updated_at', 'updated_by', 'deleted')
    list_filter = ('form', 'created_at', 'submitted_at', 'created_by', 'updated_at', 'updated_by', 'deleted')
    search_fields = ('uuid', 'original_uuid', 'parent_id', 'title', 'gps', 'path', 'form_data')
    ordering = ('-submitted_at', '-created_at')
    readonly_fields = ('submitted_at', 'created_at', 'updated_at')
    raw_id_fields = ('form', 'created_by', 'updated_by')  # Use raw ID fields for ForeignKeys
    fieldsets = (
        ('Identification', {
            'fields': ('uuid', 'original_uuid', 'parent_id')
        }),
        ('Form Information', {
            'fields': ('form', 'title', 'gps', 'path', 'form_data')
        }),
        ('Status', {
            'fields': ('deleted',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'submitted_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)