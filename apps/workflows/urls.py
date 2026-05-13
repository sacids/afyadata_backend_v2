from django.urls import path

from .views import generate_workflow_json

app_name = 'workflows'

urlpatterns = [
  
    
    
    path(
        "workflow/generate/<uuid:form_definition_id>/",
        generate_workflow_json,
        name="generate_workflow_json",
    ),
]


