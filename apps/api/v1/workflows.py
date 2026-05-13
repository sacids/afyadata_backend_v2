from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from apps.workflows.models import FormDataWorkflow, WorkflowActionLog
from apps.workflows.serializers import FormDataWorkflowSyncSerializer, WorkflowActionLogSyncSerializer
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for workflow sync to ensure 
    the 'results' and 'next' keys are always present.
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000
    
    
class WorkflowSyncViewSet(viewsets.ModelViewSet):
    queryset = FormDataWorkflow.objects.all().order_by('updated_at')
    serializer_class = FormDataWorkflowSyncSerializer
    pagination_class = StandardResultsSetPagination 

    def get_queryset(self):
        """
        DOWNSYNC: Filter by project and last_update timestamp.
        """
        queryset = FormDataWorkflow.objects.all().order_by('updated_at')
        
        project_id = self.request.query_params.get('project_id')
        last_update = self.request.query_params.get('last_update')

        if project_id:
            # Filtering through the relationship: FormData -> FormDefinition -> Project
            queryset = queryset.filter(form_data__form__project_id=project_id)
        
        if last_update:
            queryset = queryset.filter(updated_at__gt=last_update)
            
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        UPSYNC: Handle bulk upload of workflows and logs.
        """
        data = request.data
        project_id = data.get('project_id')
        workflows_data = data.get('workflows', [])
        logs_data = data.get('logs', [])

        # 1. Process Workflows
        for item in workflows_data:
            form_data_uuid = item.get('form_data_uuid')
            # Update existing or ignore if not found
            instance = FormDataWorkflow.objects.filter(form_data__uuid=form_data_uuid).first()
            if instance:
                serializer = self.get_serializer(instance, data=item, partial=True)
                if serializer.is_valid():
                    serializer.save()

        # 2. Process Logs
        for log_item in logs_data:
            # Use the specialized log serializer for creation
            log_serializer = WorkflowActionLogSyncSerializer(data=log_item)
            if log_serializer.is_valid():
                # Avoid duplicates if the ID is provided from the app
                if not WorkflowActionLog.objects.filter(id=log_item.get('id')).exists():
                    log_serializer.save()

        return Response({"status": "success", "message": "Sync completed"}, status=status.HTTP_201_CREATED)