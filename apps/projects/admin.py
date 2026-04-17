from django.contrib import admin
from .models import *



from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone


# Register your models here.
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["title"]
    ordering = ("title",)


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    ordering = ("id",)
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "code", "access", "auto_join", "active", "created_at"]
    ordering = ("id",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProjectMemberInline]
    filter_horizontal = ["tags"]
    list_per_page = 25


class FormAttachmentInline(admin.TabularInline):
    model = FormAttachment
    ordering = ("title",)
    extra = 0


class FormDataFileInline(admin.TabularInline):
    model = FormDataFile
    ordering = ("created_at",)
    extra = 0


@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "short_title",
        "version",
        "code",
        "icon_type",
        "sort_order",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
    )
    list_filter = ("created_at", "updated_at", "created_by", "updated_by")
    search_fields = ("title", "short_title", "version", "code", "description")
    ordering = ("sort_order", "-created_at")
    readonly_fields = ("created_at", "updated_at")
    inlines = [FormAttachmentInline]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "project",
                    "title",
                    "short_title",
                    "version",
                    "code",
                    "icon_type",
                    "is_root",
                    "sort_order",
                )
            },
        ),
        (
            "Form Definition Details",
            {"fields": ("xlsform", "form_defn", "description", "children")},
        ),
        (
            "Audit Information",
            {
                "fields": ("created_at", "created_by", "updated_at", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FormData)
class FormDataAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "form",
        "title",
        "created_at",
        "submitted_at",
        "created_by",
        "updated_at",
        "updated_by",
        "deleted",
    )
    list_filter = (
        "form",
        "created_at",
        "submitted_at",
        "created_by",
        "updated_at",
        "updated_by",
        "deleted",
    )
    search_fields = (
        "uuid",
        "original_uuid",
        "parent_id",
        "title",
        "gps",
        "path",
        "form_data",
    )
    ordering = ("-submitted_at", "-created_at")
    readonly_fields = ("submitted_at", "created_at", "updated_at")
    inlines = [FormDataFileInline]
    raw_id_fields = (
        "form",
        "created_by",
        "updated_by",
    )  # Use raw ID fields for ForeignKeys
    fieldsets = (
        ("Identification", {"fields": ("uuid", "original_uuid", "parent_id")}),
        ("Form Information", {"fields": ("form", "title", "gps", "path", "form_data")}),
        ("Status", {"fields": ("deleted",)}),
        (
            "Audit Information",
            {
                "fields": (
                    "created_at",
                    "created_by",
                    "updated_at",
                    "updated_by",
                    "submitted_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)




# apps/projects/admin.py


@admin.register(ProjectQRCode)
class ProjectQRCodeAdmin(admin.ModelAdmin):
    """
    Admin interface for Project QR Codes
    """
    
    # List display configuration
    list_display = [
        'id_short',
        'project_link',
        'status_badge',
        'scans_display',
        'issued_to_display',
        'expiry_status',
        'created_at_short',
    ]
    
    # Fields to filter by
    list_filter = [
        'is_active',
        'project',
        ('expires_at', admin.DateFieldListFilter),
        'created_at',
    ]
    
    # Search fields
    search_fields = [
        'project__title',
        'project__code',
        'id',
        'issued_to__username',
        'issued_to__email',
    ]
    
    # Read-only fields
    readonly_fields = [
        'id',
        'scan_count',
        'created_at',
        'qr_code_preview',
        'qr_code_link',
    ]
    
    # Fieldsets for detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'project', 'is_active')
        }),
        ('QR Code Details', {
            'fields': ('qr_code_preview', 'qr_code_link', 'scan_count')
        }),
        ('Validity Settings', {
            'fields': ('expires_at',),
            'classes': ('collapse',),
        }),
        ('Assignment', {
            'fields': ('issued_to',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    # Actions
    actions = ['activate_qr_codes', 'deactivate_qr_codes', 'extend_expiry']
    
    # List view customization
    list_per_page = 25
    date_hierarchy = 'created_at'
    list_select_related = ['project', 'issued_to']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('project', 'issued_to')
    
    # Display methods
    def id_short(self, obj):
        """Show shortened ID"""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    id_short.admin_order_field = 'id'
    
    def project_link(self, obj):
        """Link to project admin page"""
        url = reverse('admin:projects_project_change', args=[obj.project.id])
        return format_html('<a href="{}" style="font-weight: bold;">{}</a>', url, obj.project.title)
    project_link.short_description = 'Project'
    project_link.admin_order_field = 'project__title'
    
    def scans_display(self, obj):
        """Display scan count with icon"""
        if obj.scan_count > 0:
            return format_html('<span style="font-weight: bold; color: #2563eb;">🔍 {}</span>', obj.scan_count)
        return format_html('<span style="color: #6b7280;">📭 0</span>', obj.scan_count)
    scans_display.short_description = 'Scans'
    scans_display.admin_order_field = 'scan_count'
    
    def status_badge(self, obj):
        """Show status badge"""
        if obj.is_valid:
            return format_html('<span style="background-color: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✓ Active</span>')
        elif not obj.is_active:
            return format_html('<span style="background-color: #ef4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✗ Inactive</span>')
        else:
            return format_html('<span style="background-color: #f59e0b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">⚠ Expired</span>')
    status_badge.short_description = 'Status'
    
    def expiry_status(self, obj):
        """Show expiry information"""
        if not obj.expires_at:
            return format_html('<span style="color: #10b981;">Never expires</span>')
        
        now = timezone.now()
        if obj.expires_at < now:
            return format_html('<span style="color: #ef4444;">Expired: {}</span>', obj.expires_at.strftime('%Y-%m-%d'))
        elif (obj.expires_at - now).days < 7:
            return format_html('<span style="color: #f59e0b;">Expires soon: {}</span>', obj.expires_at.strftime('%Y-%m-%d'))
        else:
            return format_html('<span style="color: #6b7280;">Expires: {}</span>', obj.expires_at.strftime('%Y-%m-%d'))
    expiry_status.short_description = 'Expiry'
    expiry_status.admin_order_field = 'expires_at'
    
    def issued_to_display(self, obj):
        """Show who the QR code was issued to"""
        if obj.issued_to:
            return format_html('<span>{}</span><br><span style="color: #6b7280; font-size: 10px;">{}</span>', 
                             obj.issued_to.get_full_name() or obj.issued_to.username,
                             obj.issued_to.email)
        return format_html('<span style="color: #9ca3af;">Not assigned</span>')
    issued_to_display.short_description = 'Issued To'
    issued_to_display.admin_order_field = 'issued_to__username'
    
    def created_at_short(self, obj):
        """Show creation date in short format"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_short.short_description = 'Created'
    created_at_short.admin_order_field = 'created_at'
    
    def is_valid_display(self, obj):
        """Show validation status with details"""
        if obj.is_valid:
            return format_html('<span style="color: #10b981;">✓ Valid QR Code</span>')
        
        reasons = []
        if not obj.is_active:
            reasons.append('Inactive')
        if obj.expires_at and timezone.now() > obj.expires_at:
            reasons.append('Expired')
        
        return format_html('<span style="color: #ef4444;">✗ Invalid: {}</span>', ', '.join(reasons))
    is_valid_display.short_description = 'Validation Status'
    
    def qr_code_preview(self, obj):
        """Show QR code preview (placeholder)"""
        return format_html(
            '<div style="background-color: #f3f4f6; padding: 10px; text-align: center; border-radius: 8px;">'
            '<span style="color: #6b7280;">📱 QR Code Preview</span><br>'
            '<span style="font-size: 11px; color: #9ca3af;">ID: {}</span>'
            '</div>',
            obj.id
        )
    qr_code_preview.short_description = 'QR Code Preview'
    
    def qr_code_link(self, obj):
        """Generate QR code link"""
        if obj.project and obj.project.code:
            join_url = f"/projects/join/{obj.project.code}/"
            return format_html(
                '<a href="{}" target="_blank" style="color: #3b82f6;">'
                '🔗 Join URL: /projects/join/{}/</a>',
                join_url, obj.project.code
            )
        return format_html('<span style="color: #9ca3af;">Project code not available</span>')
    qr_code_link.short_description = 'Join Link'
    
    # Admin Actions
    def activate_qr_codes(self, request, queryset):
        """Activate selected QR codes"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} QR code(s) activated successfully.')
    activate_qr_codes.short_description = 'Activate selected QR codes'
    
    def deactivate_qr_codes(self, request, queryset):
        """Deactivate selected QR codes"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} QR code(s) deactivated successfully.')
    deactivate_qr_codes.short_description = 'Deactivate selected QR codes'
    
    def extend_expiry(self, request, queryset):
        """Extend expiry by 30 days for selected QR codes"""
        from datetime import timedelta
        updated = 0
        for qr in queryset:
            if qr.expires_at:
                qr.expires_at = qr.expires_at + timedelta(days=30)
            else:
                qr.expires_at = timezone.now() + timedelta(days=30)
            qr.save()
            updated += 1
        self.message_user(request, f'Expiry extended by 30 days for {updated} QR code(s).')
    extend_expiry.short_description = 'Extend expiry by 30 days'
    
    # Save model customizations
    def save_model(self, request, obj, form, change):
        """Auto-set issued_to when creating new QR code"""
        if not change and not obj.issued_to:
            obj.issued_to = request.user
        super().save_model(request, obj, form, change)
    
    # List view customization
    def get_list_display(self, request):
        """Customize list display based on user permissions"""
        if request.user.is_superuser:
            return self.list_display
        return [f for f in self.list_display if f not in ['id_short', 'qr_code_preview']]