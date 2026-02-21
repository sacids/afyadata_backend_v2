# views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from apps.setup.models import Language, LanguageVersion, LanguageDownload
from apps.setup.serializers import (
    LanguageSerializer,
    LanguageVersionSerializer,
    LanguageUploadSerializer,
    LanguageDownloadSerializer,
    LanguageStatsSerializer,
)
import json
from django.http import HttpResponse
from wsgiref.util import FileWrapper
import os


class LanguageViewSet(viewsets.ModelViewSet):
    """API endpoint for managing languages"""

    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            #permission_classes = [IsAdminUser]
            permission_classes = [AllowAny]
        else:
            #permission_classes = [IsAuthenticated]
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def available(self, request):
        """Get list of available languages (for mobile app)"""
        languages = self.get_queryset()
        serializer = self.get_serializer(languages, many=True)

        # Format for mobile app
        formatted_data = []
        for lang in languages:
            latest_version = (
                lang.versions.filter(is_published=True).order_by("-created_at").first()
            )
            if latest_version:
                formatted_data.append(
                    {
                        "code": lang.code,
                        "name": lang.name,
                        "nativeName": lang.native_name,
                        "version": latest_version.version,
                        "size": latest_version.file_size,
                        "updatedAt": latest_version.created_at.isoformat(),
                    }
                )

        return Response({"languages": formatted_data})

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def translations(self, request, pk=None):
        """Get translations for a specific language (for mobile app)"""
        language = self.get_object()

        # Get the latest published version
        version = request.query_params.get("version", None)
        if version:
            language_version = get_object_or_404(
                LanguageVersion, language=language, version=version, is_published=True
            )
        else:
            language_version = (
                language.versions.filter(is_published=True)
                .order_by("-created_at")
                .first()
            )

        if not language_version:
            return Response(
                {"error": "No published version available for this language"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Track download
        download_data = {
            "language": language.pk,
            "version": language_version.pk,
            "device_id": request.headers.get("X-Device-ID", ""),
            "app_version": request.headers.get("X-App-Version", ""),
        }

        if request.user.is_authenticated:
            download_data["user"] = request.user.pk

        download_serializer = LanguageDownloadSerializer(data=download_data)
        if download_serializer.is_valid():
            download = download_serializer.save()
            download.ip_address = self.get_client_ip(request)
            download.save()

        # Return translations
        return Response(language_version.translations)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, pk=None):
        """Upload a new version of language translations"""
        language = self.get_object()

        upload_serializer = LanguageUploadSerializer(data=request.data)
        if not upload_serializer.is_valid():
            return Response(
                upload_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if version already exists
        if LanguageVersion.objects.filter(
            language=language, version=upload_serializer.validated_data["version"]
        ).exists():
            return Response(
                {
                    "error": f"Version {upload_serializer.validated_data['version']} already exists"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create new version
        language_version = LanguageVersion(
            language=language,
            version=upload_serializer.validated_data["version"],
            file=upload_serializer.validated_data["file"],
            is_published=upload_serializer.validated_data.get("publish", False),
            created_by=request.user,
        )

        language_version.save()

        # If publishing, unpublish other versions of this language
        if language_version.is_published:
            LanguageVersion.objects.filter(
                language=language, is_published=True
            ).exclude(pk=language_version.pk).update(is_published=False)

        serializer = LanguageVersionSerializer(language_version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get language download statistics"""
        # Get download counts per language
        stats = Language.objects.annotate(
            download_count=Count("languagedownload")
        ).order_by("-download_count")

        serializer = LanguageStatsSerializer(stats, many=True)
        return Response(serializer.data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class LanguageVersionViewSet(viewsets.ModelViewSet):
    """API endpoint for managing language versions"""

    queryset = LanguageVersion.objects.all()
    serializer_class = LanguageVersionSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Publish a language version"""
        language_version = self.get_object()

        # Unpublish other versions of the same language
        LanguageVersion.objects.filter(
            language=language_version.language, is_published=True
        ).exclude(pk=language_version.pk).update(is_published=False)

        # Publish this version
        language_version.is_published = True
        language_version.published_at = timezone.now()
        language_version.save()

        serializer = self.get_serializer(language_version)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def download(self, request, pk=None):
        """Download language file"""
        language_version = self.get_object()

        if not language_version.is_published and not request.user.is_staff:
            return Response(
                {"error": "This version is not published"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Track download
        download_data = {
            "language": language_version.language.pk,
            "version": language_version.pk,
            "device_id": request.headers.get("X-Device-ID", ""),
            "app_version": request.headers.get("X-App-Version", ""),
        }

        if request.user.is_authenticated:
            download_data["user"] = request.user.pk

        download_serializer = LanguageDownloadSerializer(data=download_data)
        if download_serializer.is_valid():
            download = download_serializer.save()
            download.ip_address = self.get_client_ip(request)
            download.save()

        # Return file as JSON response
        return Response(language_version.translations)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


# Admin API Views
@api_view(["GET"])
@permission_classes([IsAdminUser])
def language_export(request, code):
    """Export language file for backup"""
    language = get_object_or_404(Language, code=code)
    latest_version = language.versions.filter(is_published=True).first()

    if not latest_version:
        return Response(
            {"error": "No published version available"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Create JSON file response
    response = HttpResponse(
        json.dumps(latest_version.translations, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{code}_{latest_version.version}.json"'
    )
    return response


@api_view(["POST"])
@permission_classes([IsAdminUser])
def bulk_upload(request):
    """Bulk upload multiple language files"""
    files = request.FILES.getlist("files")
    results = []

    for file in files:
        try:
            # Parse filename to get language code and version
            # Format: en-1.0.0.json or fr.json (version defaults to 1.0.0)
            filename = file.name.replace(".json", "")
            if "-" in filename:
                code, version = filename.split("-", 1)
            else:
                code = filename
                version = "1.0.0"

            # Get or create language
            language, created = Language.objects.get_or_create(
                code=code.lower(),
                defaults={"name": code.upper(), "native_name": code.upper()},
            )

            # Check if version exists
            if LanguageVersion.objects.filter(
                language=language, version=version
            ).exists():
                results.append(
                    {
                        "file": file.name,
                        "status": "error",
                        "message": f"Version {version} already exists for {code}",
                    }
                )
                continue

            # Create version
            language_version = LanguageVersion(
                language=language,
                version=version,
                file=file,
                created_by=request.user,
                is_published=request.data.get("publish", False),
            )
            language_version.save()

            results.append(
                {
                    "file": file.name,
                    "status": "success",
                    "language": code,
                    "version": version,
                    "language_id": language.pk,
                    "version_id": language_version.pk,
                }
            )

        except Exception as e:
            results.append({"file": file.name, "status": "error", "message": str(e)})

    return Response({"results": results})
