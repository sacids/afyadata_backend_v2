import logging
import requests
from django.conf import settings
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
from django.db import transaction
from apps.ohkr.serializers import *
from apps.ohkr.models import *


class SpecieView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    """API List for Species"""
    def get_serializer_class(self):
        if self.action in ["list", "featured"]:
            return SpecieSerializer
        return super().get_serializer_class()
    
    def lists(self, request):
        """Get all species"""
        species = Specie.objects.order_by('name').all()
        serializer = SpecieSerializer(species, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def details(self, request, pk=None):
        """Get specie information"""
        specie = Specie.objects.get(pk=pk)
        serializer = SpecieSerializer(specie)
        return Response(serializer.data)

    def retrieve(self, request, tags=None):
        """Get species"""
        pass    

    def create(self, request):
        """
        Pull species from FAO species API and insert/update locally
        """
        api_url = "https://reference-data-service-175434516411.europe-west1.run.app/api/species/"
        headers = {"accept": "application/json"}

        try:
            # Fetch data from remote service
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            remote_data = response.json()

            # If results are nested, e.g. {"results": [...]}, adjust here
            if isinstance(remote_data, dict) and "results" in remote_data:
                remote_data = remote_data["results"]

            if not isinstance(remote_data, list):
                return Response(
                    {"error": "Unexpected data format from remote API."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            created, updated = 0, 0
            with transaction.atomic():
                for item in remote_data:
                    # Adjust keys according to your Specie model fields
                    serializer = SpecieSerializer(data=item)
                    if serializer.is_valid():
                        obj, was_created = Specie.objects.update_or_create(
                            external_id=item.get("id"),
                            defaults=serializer.validated_data,
                        )
                        if was_created:
                            created += 1
                        else:
                            updated += 1
                    else:
                        # skip invalid entry
                        continue

            return Response(
                {
                    "message": "Species synced successfully",
                    "created": created,
                    "updated": updated,
                    "total": len(remote_data),
                },
                status=status.HTTP_201_CREATED,
            )

        except requests.RequestException as e:
            return Response(
                {"error": f"Failed to fetch species: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    

class DiseaseView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    """API List for Diseases"""
    def get_serializer_class(self):
        if self.action in ["list", "featured"]:
            return DiseaseSerializer
        return super().get_serializer_class()
    
    def lists(self, request):
        """Get all diseases"""
        diseases = Disease.objects.order_by('name').all()
        serializer = DiseaseSerializer(diseases, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def details(self, request, pk=None):
        """Get disease information"""
        disease = Disease.objects.get(pk=pk)
        serializer = DiseaseSerializer(disease)
        return Response(serializer.data)

    def retrieve(self, request, tags=None):
        """Get diseases"""
        pass    

    def create(self, request):
        """Create disease"""
        serializer = DiseaseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ClinicalSignView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    """API List for Clinical Signs"""
    def get_serializer_class(self):
        if self.action in ["list", "featured"]:
            return ClinicalSignSerializer
        return super().get_serializer_class()
    
    def lists(self, request):
        """Get all clinical signs"""
        clinical_signs = ClinicalSign.objects.order_by('name').all()
        serializer = ClinicalSignSerializer(clinical_signs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def details(self, request, pk=None):
        """Get clinical sign information"""
        clinical_sign = ClinicalSign.objects.get(pk=pk)
        serializer = ClinicalSignSerializer(clinical_sign)
        return Response(serializer.data)

    def retrieve(self, request, tags=None):
        """Get clinical sign"""
        pass    

    def create(self, request):
        """Create clinical sign"""
        serializer = ClinicalSignSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)