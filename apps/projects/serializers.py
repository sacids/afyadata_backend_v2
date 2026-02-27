from django.contrib.auth.models import User, Group
from .models import *
from rest_framework import serializers


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


class FormAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for form attachment"""

    class Meta:
        model = FormAttachment
        fields = "__all__"


class FormDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for form definition"""
    attachments = FormAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = FormDefinition
        fields = "__all__"


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
