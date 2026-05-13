from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FormDataWorkflow, WorkflowActionLog, WorkflowDefinition, WorkflowState
from apps.projects.models import FormData

User = get_user_model()

class WorkflowActionLogSyncSerializer(serializers.ModelSerializer):
    form_data_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=FormData.objects.all(),
        source='transition_form_data'
    )

    class Meta:
        model = WorkflowActionLog
        fields = [
            'id', 'form_data_uuid', 'action_name', 'from_state', 
            'to_state', 'action_by', 'metadata', 'created_at'
        ]

class FormDataWorkflowSyncSerializer(serializers.ModelSerializer):
    form_data_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=FormData.objects.all(),
        source='form_data'
    )
    # Nested logs for the downsync
    action_logs = serializers.SerializerMethodField()

    class Meta:
        model = FormDataWorkflow
        fields = [
            'id', 'form_data_uuid', 'workflow_state', 'workflow_updated_at',
            'last_action', 'is_locked', 'is_closed', 'metadata', 
            'updated_at', 'action_logs'
        ]

    def get_action_logs(self, obj):
        # Fetch logs related to this specific form data
        logs = WorkflowActionLog.objects.filter(transition_form_data=obj.form_data)
        return WorkflowActionLogSyncSerializer(logs, many=True).data