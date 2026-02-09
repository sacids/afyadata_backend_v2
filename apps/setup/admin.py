# admin.py
from django.contrib import admin
from .models import Language, LanguageVersion, LanguageDownload
from django.utils.html import format_html
import json

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'native_name', 'is_active', 'is_default', 'created_at']
    list_filter = ['is_active', 'is_default']
    search_fields = ['code', 'name', 'native_name']
    list_editable = ['is_active', 'is_default']
    actions = ['make_active', 'make_inactive', 'set_as_default']
    
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected languages as active"
    
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected languages as inactive"
    
    def set_as_default(self, request, queryset):
        # Set all languages as non-default first
        Language.objects.filter(is_default=True).update(is_default=False)
        # Set selected as default
        queryset.update(is_default=True)
    set_as_default.short_description = "Set selected as default language"

@admin.register(LanguageVersion)
class LanguageVersionAdmin(admin.ModelAdmin):
    list_display = ['language', 'version', 'file_size', 'file_hash_short', 
                    'is_published', 'created_by', 'created_at']
    list_filter = ['is_published', 'language', 'created_at']
    search_fields = ['language__code', 'language__name', 'version']
    readonly_fields = ['file_size', 'file_hash', 'created_at', 'published_at']
    actions = ['publish_versions', 'unpublish_versions', 'export_json']
    
    def file_hash_short(self, obj):
        return obj.file_hash[:10] + '...' if obj.file_hash else ''
    file_hash_short.short_description = 'Hash'
    
    def publish_versions(self, request, queryset):
        # Unpublish all versions of the languages first
        languages = queryset.values_list('language', flat=True).distinct()
        LanguageVersion.objects.filter(language__in=languages).update(is_published=False)
        
        # Publish selected versions
        queryset.update(is_published=True)
    publish_versions.short_description = "Publish selected versions"
    
    def unpublish_versions(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_versions.short_description = "Unpublish selected versions"
    
    def export_json(self, request, queryset):
        # This would typically redirect to a view that exports the JSON
        pass
    export_json.short_description = "Export selected as JSON"

@admin.register(LanguageDownload)
class LanguageDownloadAdmin(admin.ModelAdmin):
    list_display = ['language', 'version', 'user', 'device_id', 'app_version', 'downloaded_at']
    list_filter = ['language', 'downloaded_at']
    search_fields = ['language__code', 'user__username', 'device_id']
    readonly_fields = ['downloaded_at']
    date_hierarchy = 'downloaded_at'