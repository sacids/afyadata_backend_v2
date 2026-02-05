import logging
import json
from datetime import datetime, date
from django.utils.dateparse import parse_datetime
from django.utils import timezone
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

    def create(self, request, *args, **kwargs):
        """Create new form data coming from mobile app"""
        if not request.data:
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Normalize incoming data (QueryDict or dict)
        raw_data = request.data

        # DRF can give you a QueryDict or a regular dict depending on content-type
        if hasattr(raw_data, "dict"):  # QueryDict-like (form-data)
            data = raw_data.dict()
        else:  # already a normal dict (e.g. JSON body)
            data = dict(raw_data)

        try:
            # Parse form_data JSON safely
            form_data_value = data.get("form_data")

            if isinstance(form_data_value, str):
                try:
                    data["form_data"] = json.loads(form_data_value)
                except json.JSONDecodeError:
                    # If JSON is broken, log and keep it as raw string
                    logging.warning("Invalid JSON in form_data, keeping as string")
                    data["form_data"] = form_data_value
            elif form_data_value is None:
                data["form_data"] = {}
            else:
                # Already parsed (e.g. app sent JSON & DRF parsed it)
                data["form_data"] = form_data_value


            # Parse dates (created_on)
            created_on_str = data.get("created_on")
            created_on = parse_datetime(created_on_str) if created_on_str else None
            if created_on is None:
                created_on = timezone.now()

            # Normalize flags (deleted, archived, synced)
            def to_bool(val, default=False):
                if val is None:
                    return default
                return str(val).lower() in ("1", "true", "yes")

            # default to false
            deleted = to_bool(data.get("deleted"), default=False)

            # Handle photo upload (if any)
            photo = None
            if request.FILES:
                photo = save_uploaded_images(request.FILES, upload_subdir="assets/uploads/photos/")

            #  Insert or update database record
            instance, created_flag = FormData.objects.update_or_create(
                uuid=data["uuid"],
                defaults={
                    "form_data": data["form_data"],
                    "original_uuid": data.get("original_uuid", data["uuid"]),
                    "parent_id": data["parent_id"],
                    "title": data.get("title", ""),
                    "created_by_name": data.get("created_by_name", ""),
                    "form_id": data.get("form"),
                    "gps": data.get("gps"),
                    "created_at": created_on,
                    "created_by": request.user if request.user.is_authenticated else None,
                    "updated_at": timezone.now(),
                    "last_updated_at": timezone.now(),
                    "submitted_at": timezone.now(),
                    "deleted": deleted,
                    "synced": 1,
                    # only set photo if we received one
                    #**({"photo": photo} if photo is not None else {}),
                },
            )

            logging.info("== inserted/updated form data ==")
            logging.info({"id": instance.id, "uuid": instance.uuid, "created": created_flag})

            # Build response back to mobile app
            instance.refresh_from_db()

            if getattr(instance.form, "response", None):
                response_payload = {
                    "uuid": instance.uuid,
                    "synced": 1,
                    "message": instance.form.response,
                }
            else:
                response_payload = {
                    "uuid": instance.uuid,
                    "synced": 1,
                    "message": "Form data created successfully" if created_flag else "Form data updated successfully",
                }

            # Return Response
            logging.info("== Success creating form data ==")
            return Response({"success": True, "data": response_payload}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logging.exception("== Error creating form data ==")
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
