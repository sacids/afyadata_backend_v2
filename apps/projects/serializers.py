from django.contrib.auth.models import Group
from .models import *
from rest_framework import serializers


from django.contrib.auth import get_user_model
User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(many=False)
    updated_by = serializers.StringRelatedField(many=False)
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = Project
        fields = "__all__"


class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = "__all__"


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = [
            "id",
            "project",
            "title",
            "description",
            "photo",
            "photo_url",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = fields

    def get_photo_url(self, obj):
        if not obj.photo:
            return ""

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.photo.url)
        return obj.photo.url


class FormAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for form attachment"""

    class Meta:
        model = FormAttachment
        fields = "__all__"


class FormDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for form definition"""
    attachments = FormAttachmentSerializer(many=True, read_only=True)
    icon = serializers.SerializerMethodField()

    class Meta:
        model = FormDefinition
        fields = "__all__"

    def get_icon(self, obj):
        return obj.icon_type


class FormDefnMetaSerializer(serializers.ModelSerializer):
    """Serializer for form definition"""
    attachments = FormAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = FormDefinition
        fields = ["id", "version", "short_title", "attachments"]


class FormDataSerializer(serializers.ModelSerializer):
    """Serializer for form data"""
    class Meta:
        model = FormData
        fields = "__all__"
