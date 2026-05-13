import uuid
from django.db import models

# from django.contrib.gis.db import models  # Use GIS models

from django.contrib.auth.validators import UnicodeUsernameValidator
#from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from apps.projects.models import FormDefinition, FormData

from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _


from django.contrib.auth import get_user_model
User = get_user_model()





class WorkflowDefinition(models.Model):
    """
    Main workflow container.
    Example:
        Incident Management
        Sample Review Workflow
        Tobacco Inspection Workflow
    """

    form_definition = models.OneToOneField(
        FormDefinition,
        on_delete=models.CASCADE,
        related_name="workflow",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    code = models.SlugField(unique=True)

    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkflowState(models.Model):
    """
    States inside a workflow.
    Example:
        Draft
        Submitted
        Reviewed
        Approved
        Rejected
    """

    workflow = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="states"
    )

    name = models.CharField(max_length=255)

    code = models.SlugField()

    description = models.TextField(blank=True, null=True)

    is_initial = models.BooleanField(default=False)

    is_final = models.BooleanField(default=False)

    color = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Optional UI color"
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="entypo:clipboard",
        help_text="Optional icon name"
    )

    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = ("workflow", "code")

    def save(self, *args, **kwargs):
        """
        Ensure only one initial state per workflow.
        """

        super().save(*args, **kwargs)

        if self.is_initial:
            WorkflowState.objects.filter(
                workflow=self.workflow,
                is_initial=True
            ).exclude(id=self.id).update(is_initial=False)

    def __str__(self):
        return f"{self.workflow.name} - {self.name}"


class WorkflowTransition(models.Model):
    """
    Defines movement from one state to another.

    Example:
        Draft -> Submit -> Submitted
        Submitted -> Approve -> Approved
        Submitted -> Reject -> Rejected
    """

    workflow = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="transitions"
    )

    from_state = models.ManyToManyField(
        WorkflowState,
        related_name="outgoing_transitions"
    )

    to_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.CASCADE,
        related_name="incoming_transitions"
    )

    action_name = models.CharField(
        max_length=255,
        help_text="Human readable action name"
    )

    action_code = models.SlugField(
        help_text="Machine readable action code"
    )
    
    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="MaterialIcons:play-circle-outline",
        help_text="Optional icon name"
    )

    description = models.TextField(blank=True, null=True)
    
    transition_form = models.ForeignKey(
        FormDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_transition_forms",
        help_text="Optional form required before executing transition"
    )

    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="workflow_transitions",
        help_text="Groups allowed to execute this transition"
    )

    allow_offline = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        unique_together = (
            "workflow",
            "to_state",
            "action_code",
        )

    def __str__(self):
        return (
            f"{self.from_state.name} "
            f"--({self.action_name})--> "
            f"{self.to_state.name}"
        )

    def user_can_execute(self, user):
        """
        Checks if user can execute transition.
        """

        if not user.is_authenticated:
            return False

        # Superuser bypass
        if user.is_superuser:
            return True

        # Check group membership
        transition_groups = self.groups.all()

        if transition_groups.exists():
            user_group_ids = user.groups.values_list("id", flat=True)

            if not transition_groups.filter(
                id__in=user_group_ids
            ).exists():
                return False


        return True


class WorkflowActionLog(models.Model):
    """
    Audit trail for workflow actions.

    Example:
        User X approved form
        User Y rejected form
    """

    workflow = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.CASCADE,
        related_name="logs"
    )

    transition = models.ForeignKey(
        WorkflowTransition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    from_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+"
    )

    to_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+"
    )

    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action_name = models.CharField(max_length=255)

    transition_form_data = models.ForeignKey(
        FormData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_transition_logs"
    )

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.transition_form_data} - "
            f"{self.action_name} - "
            f"{self.created_at}"
        )
        
        
        


class FormDataWorkflow(models.Model):
    """
    Runtime workflow state for a submitted form.

    This stores ONLY the CURRENT workflow state.

    Full audit trail/history is stored separately
    in WorkflowActionLog.
    """

    form_data = models.OneToOneField(
        FormData,
        on_delete=models.CASCADE,
        related_name="workflow"
    )

    # ---------------------------------------------------
    # CURRENT WORKFLOW STATE
    # ---------------------------------------------------

    workflow_state = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Current workflow state code"
    )

    workflow_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )

    workflow_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_form_workflows"
    )

    # ---------------------------------------------------
    # CURRENT ASSIGNMENT
    # ---------------------------------------------------

    assigned_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_workflows",
        help_text="Current responsible group"
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_form_workflows",
        help_text="Current responsible user"
    )

    # ---------------------------------------------------
    # LAST ACTION
    # ---------------------------------------------------

    last_action = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Last executed workflow action"
    )

    # ---------------------------------------------------
    # WORKFLOW FLAGS
    # ---------------------------------------------------

    is_locked = models.BooleanField(
        default=False,
        help_text="Prevent further editing"
    )

    is_closed = models.BooleanField(
        default=False,
        help_text="Workflow completed/closed"
    )

    escalation_level = models.PositiveIntegerField(
        default=0
    )

    reopened_count = models.PositiveIntegerField(
        default=0
    )

    # ---------------------------------------------------
    # SLA / DEADLINES
    # ---------------------------------------------------

    due_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # ---------------------------------------------------
    # EXTRA METADATA
    # ---------------------------------------------------

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    # ---------------------------------------------------
    # AUDIT
    # ---------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "ad_form_data_workflows"

        verbose_name = "Form Data Workflow"

        verbose_name_plural = "Form Data Workflows"

        indexes = [
            models.Index(fields=["workflow_state"]),
            models.Index(fields=["workflow_updated_at"]),
            models.Index(fields=["assigned_group"]),
            models.Index(fields=["assigned_to"]),
            models.Index(fields=["is_closed"]),
            models.Index(fields=["is_locked"]),
            models.Index(fields=["due_at"]),
        ]

    def __str__(self):
        return (
            f"{self.form_data_id} - "
            f"{self.workflow_state}"
        )

    # ===================================================
    # INITIALIZATION
    # ===================================================

    @classmethod
    def initialize_for_form_data(
        cls,
        form_data,
        config,
        user=None
    ):
        """
        Creates workflow runtime instance
        using workflow initial state.
        """
        if not config or not config.get("enabled"):
            return None

        # config is a dict, so use config.get("states") instead of config.states
        states = config.get("states", [])
        
        # Find the state dictionary where "initial" is True
        initial_state_data = next((s for s in states if s.get("initial") is True), None)

        if not initial_state_data:
            raise Exception(
                f"Workflow '{config.get('name')}' has no initial state defined in JSON"
            )

        return cls.objects.create(
            form_data=form_data,

            workflow_state=initial_state_data["code"],

            workflow_updated_at=timezone.now(),

            workflow_updated_by=user,
        )

    # ===================================================
    # ASSIGNMENT HELPERS
    # ===================================================

    def assign_to_user(self, user):

        self.assigned_to = user

        self.save(
            update_fields=[
                "assigned_to",
                "updated_at",
            ]
        )

    def assign_to_group(self, group):

        self.assigned_group = group

        self.save(
            update_fields=[
                "assigned_group",
                "updated_at",
            ]
        )

    # ===================================================
    # LOCKING HELPERS
    # ===================================================

    def lock(self):

        self.is_locked = True

        self.save(
            update_fields=[
                "is_locked",
                "updated_at",
            ]
        )

    def unlock(self):

        self.is_locked = False

        self.save(
            update_fields=[
                "is_locked",
                "updated_at",
            ]
        )

    # ===================================================
    # CLOSE HELPERS
    # ===================================================

    def close(self):

        self.is_closed = True

        self.save(
            update_fields=[
                "is_closed",
                "updated_at",
            ]
        )

    # ===================================================
    # STATE UPDATE
    # ===================================================

    def set_state(
        self,
        state_code,
        user=None,
        action=None
    ):

        self.workflow_state = state_code

        self.workflow_updated_at = timezone.now()

        self.workflow_updated_by = user

        if action:
            self.last_action = action

        self.save(
            update_fields=[
                "workflow_state",
                "workflow_updated_at",
                "workflow_updated_by",
                "last_action",
                "updated_at",
            ]
        )

    # ===================================================
    # UTILITIES
    # ===================================================

    @property
    def is_overdue(self):

        if not self.due_at:
            return False

        return timezone.now() > self.due_at
        
        
