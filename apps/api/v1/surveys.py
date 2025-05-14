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

from apps.projects.serializers import *
from django.db.models import Q
from django.contrib.auth.models import User
from apps.projects.models import FormDefinition


class FormDefinitionView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    """API List for Form Definition"""
    def get_serializer_class(self):
        if self.action in ["list", "featured"]:
            return FormDefinitionSerializer
        return super().get_serializer_class()
    
    def lists(self, request, project_id=None):
        """Get all form definition"""
        form_definition = FormDefinition.objects.filter(project_id=project_id).order_by('created_at').all()
        serializer = FormDefinitionSerializer(form_definition, many=True)
        return Response(serializer.data)
    
    def listMeta(self, request, project_id=None):
        """Get all form definition (id,version, short title) that user is permitted to access"""
        form_definition = FormDefinition.objects.filter(project_id=project_id).values('id','version','short_title').distinct()
        serializer = FormDefnMetaSerializer(form_definition, many=True)
        return Response(serializer.data)

    def getForm(self, request, pk=None):
        """Get form definition information"""
        form_definition = FormDefinition.objects.get(pk=pk)
        serializer = FormDefinitionSerializer(form_definition)
        return Response(serializer.data)

    def retrieve(self, request, project_id=None):
        """Get form definition"""
        form_definition = FormDefinition.objects.filter(project_id=project_id).all()
        serializer = FormDefinitionSerializer(form_definition, many=True)
        return Response(serializer.data)    

    def create(self, request):
        """Create new form definition"""
        serializer = FormDefinitionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)