import logging
from datetime import datetime, date
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.db.models import Q

from apps.projects.serializers import *
from apps.projects.models import FormDefinition
from apps.accounts.utils import is_admin_user

from django.contrib.auth import get_user_model
User = get_user_model()


class FormDefinitionView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    """API List for Form Definition"""
    def get_serializer_class(self):
        if self.action in ["list", "featured"]:
            return FormDefinitionSerializer
        return super().get_serializer_class()
    
    def _get_accessible_forms_queryset(self, user, project_id):
        """
        Helper method to filter FormDefinitions based on user permissions.
        Superusers/Admins can see everything under the project context.
        Standard users see forms with no restrictive groups OR forms explicitly open to their Groups.
        """
        base_queryset = FormDefinition.objects.filter(project_id=project_id)
        
        if is_admin_user(user):
            return base_queryset
            
        # Standard structural query filter logic
        user_groups = user.groups.all()
        return base_queryset.filter(
            Q(permitted_groups__in=user_groups)
        ).distinct()

    def lists(self, request, project_id=None):
        """Get all permitted form definitions"""
        queryset = self._get_accessible_forms_queryset(request.user, project_id)
        form_definition = queryset.order_by('created_at')
        serializer = FormDefinitionSerializer(form_definition, many=True)
        return Response(serializer.data)
    
    def listMeta(self, request, project_id=None):
        """Get all form definition meta variables (id, version, short title) that user is permitted to access"""
        queryset = self._get_accessible_forms_queryset(request.user, project_id)
        form_definition = queryset.values('id', 'version', 'short_title').distinct()
        serializer = FormDefnMetaSerializer(form_definition, many=True)
        return Response(serializer.data)

    def getForm(self, request, pk=None):
        """Get form definition information securely verifying Group authorization restrictions"""
        try:
            form_definition = FormDefinition.objects.get(pk=pk)
            
            # Enforce inline membership access assertion check for individual records
            if not is_admin_user(request.user):
                has_group_restriction = form_definition.permitted_groups.exists()
                if has_group_restriction:
                    user_groups = request.user.groups.all()
                    matches_group = form_definition.permitted_groups.filter(id__in=user_groups).exists()
                    if not matches_group:
                        return Response(
                            {"success": False, "message": "You do not have group permission clearance to view this form definition"}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            serializer = FormDefinitionSerializer(form_definition)
            return Response(serializer.data)
        except FormDefinition.DoesNotExist:
            return Response({"success": False, "message": "Form not found"}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, project_id=None):
        """Get project scoped form definitions tailored to permitted group assignments"""
        queryset = self._get_accessible_forms_queryset(request.user, project_id)
        serializer = FormDefinitionSerializer(queryset, many=True)
        return Response(serializer.data)    

    def create(self, request):
        """Create new form definition"""
        serializer = FormDefinitionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)