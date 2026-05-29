
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import *


# =========================================================
# INLINE: STATES
# =========================================================

class WorkflowStateInline(admin.TabularInline):
    model = WorkflowState

    extra = 0

    fields = (
        "sort_order",
        "name",
        "code",
        "is_initial",
        "is_final",
        "color",
        "icon",
    )

    ordering = ("sort_order",)

    show_change_link = True


# =========================================================
# INLINE: TRANSITIONS
# =========================================================

class WorkflowTransitionInline(admin.TabularInline):
    model = WorkflowTransition

    extra = 0

    fields = (
        "action_name",
        "action_code",
        "from_state",
        "to_state",
        "allow_offline",
        "is_active",
    )

    show_change_link = True


# =========================================================
# WORKFLOW DEFINITION ADMIN
# =========================================================

@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "form_definition",
        "is_active",
        "states_count",
        "transitions_count",
        "generate_json_button",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "code",
        "form_definition__title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [
        WorkflowStateInline,
        WorkflowTransitionInline,
    ]

    fieldsets = (
        (
            "Workflow Information",
            {
                "fields": (
                    "form_definition",
                    "name",
                    "code",
                    "description",
                    "is_active",
                )
            },
        ),

        (
            "Audit",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def states_count(self, obj):
        return obj.states.count()

    states_count.short_description = "States"

    def transitions_count(self, obj):
        return obj.transitions.count()

    transitions_count.short_description = "Transitions"

    def generate_json_button(self, obj):

        if not obj.form_definition:
            return "-"

        url = reverse(
            "workflows:generate_workflow_json",
            args=[obj.form_definition.id]
        )

        return format_html(
            '<a class="button" href="{}">'
            'Generate JSON'
            '</a>',
            url
        )

    generate_json_button.short_description = "Workflow JSON"


# =========================================================
# WORKFLOW STATE ADMIN
# =========================================================

@admin.register(WorkflowState)
class WorkflowStateAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "workflow",
        "is_initial",
        "is_final",
        "sort_order",
    )

    list_filter = (
        "workflow",
        "is_initial",
        "is_final",
    )

    search_fields = (
        "name",
        "code",
        "workflow__name",
    )

    ordering = (
        "workflow",
        "sort_order",
    )

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "workflow",
                    "name",
                    "code",
                    "description",
                )
            },
        ),

        (
            "Workflow Behaviour",
            {
                "fields": (
                    "is_initial",
                    "is_final",
                    "sort_order",
                )
            },
        ),

        (
            "UI Display",
            {
                "classes": ("collapse",),
                "fields": (
                    "color",
                    "icon",
                )
            },
        ),
    )


# =========================================================
# WORKFLOW TRANSITION ADMIN
# =========================================================

@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):

    list_display = (
        "action_name",
        "workflow",
        "display_from_states",
        "to_state",
        "is_active",
        "allow_offline",
    )

    list_filter = (
        "workflow",
        "is_active",
        "allow_offline",
    )

    search_fields = (
        "action_name",
        "action_code",
        "workflow__name",
    )

    filter_horizontal = (
        "from_state",
        "groups",
    )

    fieldsets = (
        (
            "Transition Information",
            {
                "fields": (
                    "workflow",
                    "action_name",
                    "action_code",
                    "icon_name",
                    "icon_color",
                    "transition_form",
                    "description",
                )
            },
        ),

        (
            "State Movement",
            {
                "fields": (
                    "from_state",
                    "to_state",
                )
            },
        ),

        (
            "Permissions",
            {
                "fields": (
                    "groups",
                )
            },
        ),

        (
            "Behaviour",
            {
                "fields": (
                    "allow_offline",
                    "is_active",
                )
            },
        ),
    )

    def display_from_states(self, obj):

        return ", ".join(
            obj.from_state.values_list(
                "name",
                flat=True
            )
        )

    display_from_states.short_description = "From States"


# =========================================================
# WORKFLOW ACTION LOG ADMIN
# =========================================================

@admin.register(WorkflowActionLog)
class WorkflowActionLogAdmin(admin.ModelAdmin):

    list_display = (
        "workflow",
        "action_name",
        "from_state",
        "to_state",
        "action_by",
        "created_at",
    )

    list_filter = (
        "workflow",
        "action_name",
        "created_at",
    )

    search_fields = (
        "action_name",
        "action_by__username",
    )

    readonly_fields = (
        "workflow",
        "transition",
        "from_state",
        "to_state",
        "action_by",
        "action_name",
        "transition_form_data",
        "metadata",
        "created_at",
    )

    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False





class WorkflowActionLogInline(admin.TabularInline):
    """Allows viewing the audit trail directly from the runtime workflow page."""
    model = WorkflowActionLog
    extra = 0
    readonly_fields = (
        "transition", "from_state", "to_state", 
        "action_by", "action_name", "created_at"
    )
    can_delete = False
    ordering = ("-created_at",)

@admin.register(FormDataWorkflow)
class FormDataWorkflowAdmin(admin.ModelAdmin):
    # --- List View Configuration ---
    list_display = (
        "form_data_link", 
        "workflow_state_badge", 
        "assigned_to", 
        "is_locked", 
        "is_closed", 
        "due_at_status",
    )
    
    list_filter = (
        "workflow_state",
        "is_locked",
        "is_closed",
        "assigned_group",
    )
    
    search_fields = (
        "form_data__uuid", 
        "form_data__title", 
        "workflow_state", 
        "assigned_to__username"
    )
    
    readonly_fields = ("created_at", "updated_at")
    
    #inlines = [WorkflowActionLogInline]

    # --- Detail View Configuration ---
    fieldsets = (
        ("Core Context", {
            "fields": ("form_data", )
        }),
        ("Current Status", {
            "fields": (
                "workflow_state", 
                "last_action", 
            )
        }),
        ("Assignment", {
            "fields": ("assigned_group", "assigned_to", "due_at")
        }),
        ("Flags & Metrics", {
            "fields": (
                "is_locked", 
                "is_closed", 
                "escalation_level", 
                "reopened_count"
            )
        }),
        ("Data", {
            "classes": ("collapse",),
            "fields": ("metadata", "created_at", "updated_at"),
        }),
    )

    # --- Custom Display Methods ---
    def form_data_link(self, obj):
        """Displays the Form Data ID or Title."""
        return obj.form_data.title or obj.form_data.uuid
    form_data_link.short_description = "Form Data"

    def workflow_state_badge(self, obj):
        """Adds a visual cue for the current state."""
        colors = {
            "submitted": "#6c757d",
            "completed": "#28a745",
            "rejected": "#dc3545",
            "reviewed": "#17a2b8"
        }
        color = colors.get(obj.workflow_state, "#007bff")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px;">{}</span>',
            color,
            obj.workflow_state
        )
    workflow_state_badge.short_description = "State"

    def due_at_status(self, obj):
        """Shows if the workflow is overdue based on the model property."""
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">Overdue</span>')
        return obj.due_at or "-"
    due_at_status.short_description = "SLA Status"

