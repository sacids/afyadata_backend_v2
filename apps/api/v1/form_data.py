import logging
import json
from datetime import datetime, date
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.projects.serializers import *
from django.db.models import Q
from django.contrib.auth.models import User
from apps.projects.models import FormData
from apps.projects.utils import save_uploaded_images


class FormDataView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    """API List for Form Data"""

    def get_serializer_class(self):
        if self.action in ["list", "featured"]:
            return FormDataSerializer()
        return super().get_serializer_class()

    def lists(self, request):
        """Get all form data"""
        form_data = FormData.objects.order_by("created_at").all()
        serializer = FormDataSerializer(form_data, many=True)
        return Response(serializer.data)

    def detail(self, request, pk=None):
        """Get form data information"""
        pass

    def retrieve(self, request):
        """Get form data based on form definition"""
        try:
            user = request.user

            # filter data based on user
            form_data = FormData.objects.filter(created_by=user, deleted=0).all()
            serializer = FormDataSerializer(form_data, many=True)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request):
        """Create new form data"""
        if request.data:
            arr_response = []
            data = request.data

            try:
                if "form_data" in data:
                    data["form_data"] = json.loads(data["form_data"])
                    logging.info(data["form_data"])

                photo = None
                if request.FILES:
                    # save uploaded images
                    photo = save_uploaded_images(request.FILES, upload_subdir="assets/uploads/photos/")

                logging.info("== reached hapa")

                # insert or update data
                form_data = FormData.objects.update_or_create(
                    uuid=data["uuid"],
                    defaults={
                        "form_data": data["form_data"],
                        "original_uuid": data["original_uuid"],
                        "title": data["title"],
                        "created_by_name": data["created_by_name"],
                        "form_id": data["form"],
                        "gps": data["gps"],
                        "created_at": data["created_on"],
                        "created_by": request.user,
                        "updated_at": datetime.now(),
                        "last_updated_at": datetime.now(),
                        "submitted_at": datetime.now(),
                        "deleted": data["deleted"],
                        "synced": 1,
                    },
                )

                logging.info("== form data ==")
                logging.info(form_data)

                # save photo
                if photo is not None:
                    FormData.objects.filter(uuid=data["uuid"]).update(photo=photo)

                # get default response from form definition
                form_data = FormData.objects.get(uuid=data["uuid"])

                if form_data.form.response:
                    response = {
                        "uuid": data["uuid"],
                        "synced": 1,
                        "message": form_data.form.response,
                    }
                    return Response(
                        {"success": True, "data": response}, status=status.HTTP_201_CREATED,
                    )

                return Response(
                    {"uuid": data["uuid"], "synced": 1, "message": "Form data created successfully"},
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                logging.info("== Error creating form data ==")
                logging.info(str(e))
                return Response(
                    {"success": False, "message": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
