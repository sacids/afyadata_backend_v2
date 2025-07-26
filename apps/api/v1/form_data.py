import logging
from datetime import datetime, date
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
        # TODO: check if project accept the data at the moment
        logging.info("==Request Data ==")
        logging.info(request.data)

        if request.data:
            arr_response = []
            for val in request.data:
                serializer = FormDataSerializer(data=val)
                try:
                    if serializer.is_valid():
                        # insert or update data
                        #print('val',val)
                        form_data_create_update = FormData.objects.update_or_create(
                            uuid=val["uuid"],
                            defaults={
                                "form_data": val["form_data"],
                                "original_uuid": val["original_uuid"],
                                "path": val["path"],
                                "parent_id": val["parent_id"],
                                "created_by_name": val["created_by_name"],
                                "form_id": val["form"],
                                "gps": val["gps"],
                                "created_at": val["created_at"],
                                "created_by": request.user,
                                "updated_at": "",
                                "deleted": val["deleted"],
                                "synced": 1,
                            },
                        )
                        # create reponse
                        res = {"uuid": val["uuid"], "synced": 1, "message": "success"}
                        print('result',res)
                        arr_response.append(res)
                    else:
                        res = {
                            "uuid": val["uuid"],
                            "synced": 0,
                            "message": str(serializer.errors),
                        }
                        print('result else',res)
                        arr_response.append(res)
                except Exception as e:
                    print('result error',e)
                    logging.info("==Errors ==")
                    logging.info(e)
            return Response({"success": True, "data": arr_response}, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
