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
from apps.projects.models import Project, ProjectMember


class ProjectView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    """API List for Project"""
    def get_serializer_class(self):
        if self.action in ["list", "featured"]:
            return ProjectSerializer
        return super().get_serializer_class()
    
    def lists(self, request):
        """Get all projects"""
        projects = Project.objects.filter(access='public').order_by('created_at').all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def details(self, request, pk=None):
        """Get project information"""
        project = Project.objects.get(pk=pk)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def retrieve(self, request, tags=None):
        """Get projects by tags"""
        projects = Project.objects.filter(tags__title__in=tags).order_by('created_at').all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)    

    def create(self, request):
        """Create new form definition"""
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def request_access(self, request):
        """Request access to project"""
        try:
            project = Project.objects.get(code=request.data['code'])

            # check if user is already a member
            if ProjectMember.objects.filter(project=project, member=request.user, active=True).exists():
                return Response({"error": False, "message": "You are already a member of this project"},status=status.HTTP_200_OK)
            else:
                # check if project is auto_join is true
                if project.auto_join:
                    ProjectMember.objects.create(project=project, member=request.user, active=True)
                    return Response({"error": False, "message": "You have been added to this project"},status=status.HTTP_200_OK)
                else:
                    ProjectMember.objects.create(project=project, member=request.user, active=False)

                    # TODO: send notification to project owner

                    # response
                    return Response({"error": False, "message": "You need to request access to this project"},status=status.HTTP_200_OK)
        except:
            return Response({"error": True, "message": "Project does not exist"},status=status.HTTP_200_OK)