import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from apps.projects.models import FormDefinition, FormData
from .models import WorkflowDefinition


@staff_member_required
@transaction.atomic
def generate_workflow_json(request, form_definition_id):
    """
    Generates workflow JSON from workflow models
    and injects it into form_defn.workflow
    """

    form_definition = get_object_or_404(
        FormDefinition,
        id=form_definition_id
    )

    workflow = get_object_or_404(
        WorkflowDefinition.objects.prefetch_related(
            "states",
            "transitions__groups",
            "transitions__from_state",
            "transitions__to_state",
        ),
        form_definition=form_definition
    )

    # -----------------------------
    # Existing Form JSON
    # -----------------------------
    try:
        form_json = json.loads(form_definition.form_defn or "{}")
    except json.JSONDecodeError:
        messages.error(
            request,
            "Invalid form_defn JSON"
        )
        return redirect(request.META.get("HTTP_REFERER"))

    # -----------------------------
    # Build States
    # -----------------------------
    states = []

    for state in workflow.states.all().order_by("sort_order"):

        states.append({
            "code": state.code,
            "label": state.name,
            "description": state.description,
            "initial": state.is_initial,
            "final": state.is_final,
            "color": state.color,
            "icon": state.icon,
            "sort_order": state.sort_order,
        })

    # -----------------------------
    # Build Transitions
    # -----------------------------
    transitions = []

    for transition in workflow.transitions.filter(
        is_active=True
    ):

        transitions.append({
            "action": transition.action_code,
            "label": transition.action_name,

            "from": list(
                transition.from_state.values_list(
                    "code",
                    flat=True
                )
            ),

            "to": transition.to_state.code,

            "groups": list(
                transition.groups.values_list(
                    "name",
                    flat=True
                )
            ),

            "transition_form_id": str(transition.transition_form.id) if transition.transition_form else None,

            "allow_offline": transition.allow_offline,

            "description": transition.description,
        })

    # -----------------------------
    # Build Workflow JSON
    # -----------------------------
    workflow_json = {
        "enabled": True,

        "code": workflow.code,

        "name": workflow.name,

        "description": workflow.description,

        "states": states,

        "transitions": transitions,
    }
    
    print("Generated Workflow JSON:", json.dumps(workflow_json, indent=2))

    # -----------------------------
    # Attach To Form JSON
    # -----------------------------
    form_json["workflow"] = workflow_json

    # Save back
    form_definition.form_defn = json.dumps(
        form_json,
        indent=2
    )

    form_definition.save(
        update_fields=[
            "form_defn",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"Workflow JSON generated for '{form_definition.title}'"
    )

    return redirect(
        request.META.get("HTTP_REFERER")
    )
    
    
    
    
    
    
    
