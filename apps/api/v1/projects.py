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
from apps.accounts.utils import is_admin_user
from apps.projects.models import KnowledgeBase, Project, ProjectMember



from django.contrib.auth import get_user_model
User = get_user_model()

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
        projects = Project.objects.filter(access="public").order_by("created_at").all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def active(self, request):
        """Get all active projects the current user is a member of."""
        projects = (
            Project.objects.filter(
                members__member=request.user,
                members__active=True,
                deleted=False,
            )
            .distinct()
            .order_by("created_at")
        )
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def details(self, request, pk=None):
        """Get project information"""
        project = Project.objects.get(pk=pk)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def retrieve(self, request, tags=None):
        """Get projects by tags"""
        projects = (
            Project.objects.filter(tags__title__in=tags).order_by("created_at").all()
        )
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Create new form definition"""
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def information(self, request):
        """Get project informationusing code"""
        code = request.data.get("code")
        if not code:
            return Response(
                {"error": True, "message": "Missing project code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            project = Project.objects.get(code=request.data["code"])
            serializer = ProjectSerializer(project)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": True, "message": "Project does not exist"},
                status=status.HTTP_200_OK,
            )

    def request_access(self, request):
        """Request access to project"""
        code = request.data.get("code")
        if not code:
            return Response(
                {"error": True, "message": "Missing project code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            project = Project.objects.get(code=request.data["code"])

            # check if user is already a member
            if ProjectMember.objects.filter(project=project, member=request.user, active=True).exists():
                # Return project details
                project_data = ProjectSerializer(project).data  # or build a dict manually

                # response
                return Response(
                    {
                        "error": False,
                        "message": "You are already a member of this project",
                        "project": project_data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # first check if is private
                if project.access == "private":
                    ProjectMember.objects.create(project=project, member=request.user, active=True, credibility_score=50)

                    # response
                    return Response(
                        {
                                "error": False, 
                                "message": "Your request has approved",
                                "project": project_data   
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    # check if project is auto_join is true
                    if project.auto_join:
                        ProjectMember.objects.create(project=project, member=request.user, active=True,credibility_score=50)

                        # response
                        return Response(
                        {
                                "error": False, 
                                "message": "Your request has approved",
                                "project": project_data   
                        },
                            status=status.HTTP_200_OK,
                        )
                    else:
                        ProjectMember.objects.create(project=project, member=request.user, active=False)

                        # TODO: send notification to project owner

                        # response
                        return Response(
                            {
                                "error": False,
                                "message": "Your request received, awaiting approval",
                            },
                            status=status.HTTP_200_OK,
                        )
                        
        except Exception as e:
            import traceback
            traceback.print_exc() 
            
            return Response(
                {
                    "error": True, 
                    "message": f"An error occurred: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, # Return 500 for actual server errors
            )
            
        # except:
        #     return Response(
        #         {"error": True, "message": "Project does not exist"},
        #         status=status.HTTP_200_OK,
        #     )

    def join(self, request, pk=None):
        """Request access to project"""
        if not pk:
            return Response(
                {"error": True, "message": "Missing project id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            project = Project.objects.get(id=pk)
            # Return project details
            project_data = ProjectSerializer(project, context={"request": request}).data

            # check if user is already a member
            if ProjectMember.objects.filter(project=project, member=request.user, active=True).exists():


                # response
                return Response(
                    {
                        "error": False,
                        "message": "You are already a member of this project",
                        "project": project_data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # first check if is private
                if project.access == "private":
                    ProjectMember.objects.update_or_create(project=project, member=request.user, active=True, credibility_score=50)

                    # response
                    return Response(
                        {
                                "error": False, 
                                "message": "Your request has approved",
                                "project": project_data   
                        },
                        status=status.HTTP_200_OK,
                    )

                else:
                    # check if project is auto_join is true
                    if project.auto_join:
                        ProjectMember.objects.update_or_create(project=project, member=request.user, active=True, credibility_score=50)

                        # response
                        return Response(
                            {
                                "error": False,
                                "message": "Your request has approved",
                                "project": project_data,
                            },
                            status=status.HTTP_200_OK,
                        )
                    else:
                        ProjectMember.objects.update_or_create(project=project, member=request.user, active=False, credibility_score=50)

                        # TODO: send notification to project owner

                        # response
                        return Response(
                            {
                                "error": False,
                                "message": "Your request received, awaiting approval",
                            },
                            status=status.HTTP_200_OK,
                        )
                        
        except Exception as e:
            import traceback
            traceback.print_exc() 
            
            return Response(
                {
                    "error": True, 
                    "message": f"An error occurred: {str(e)}"
                },
                status=status.HTTP_200_OK, # Return 500 for actual server errors
            )

    def unsubscribe(self, request, pk=None):
        """Unsubscribe from project"""
        code = request.data.get("code")
        if not code:
            return Response(
                {"error": True, "message": "Missing project code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            project = Project.objects.get(code=request.data["code"])

            # check if user is already a member
            if ProjectMember.objects.filter(project=project, member=request.user, active=True).exists():
                # unsubscribe
                ProjectMember.objects.filter(project=project, member=request.user).delete()

                # response
                return Response(
                    {
                        "error": False,
                        "message": "You have unsubscribed from this project",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": True, "message": "You are not a member of this project"},
                    status=status.HTTP_200_OK,
                )
        except:
            return Response(
                {"error": True, "message": "Project does not exist"},
                status=status.HTTP_200_OK,
            )


class KnowledgeBaseView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_accessible_project(self, request, project_id):
        project = Project.objects.filter(pk=project_id, deleted=False).first()
        if not project:
            raise Project.DoesNotExist

        if is_admin_user(request.user):
            return project

        if ProjectMember.objects.filter(
            project=project,
            member=request.user,
            active=True,
        ).exists():
            return project

        raise PermissionError("You do not have access to this project")

    def lists(self, request, project_id=None):
        try:
            self._get_accessible_project(request, project_id)
        except Project.DoesNotExist:
            return Response(
                {"success": False, "message": "Project does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        knowledge_base = (
            KnowledgeBase.objects.filter(project_id=project_id)
            .select_related("project", "created_by", "updated_by")
            .order_by("-updated_at", "title")
        )
        serializer = KnowledgeBaseSerializer(
            knowledge_base,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def detail(self, request, project_id=None, pk=None):
        try:
            self._get_accessible_project(request, project_id)
        except Project.DoesNotExist:
            return Response(
                {"success": False, "message": "Project does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        knowledge_base = KnowledgeBase.objects.filter(
            project_id=project_id,
            pk=pk,
        ).select_related("project", "created_by", "updated_by").first()
        if not knowledge_base:
            return Response(
                {"success": False, "message": "Knowledge base does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = KnowledgeBaseSerializer(
            knowledge_base,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
