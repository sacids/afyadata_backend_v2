from django.contrib.auth.models import User, Group
from .models import *
from rest_framework import serializers


class ProjectSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(many=False)
    updated_by = serializers.StringRelatedField(many=False)
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = Project
        fields = '__all__'

class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = '__all__'


class FormDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for form definition"""
    class Meta:
        model = FormDefinition
        fields = "__all__"

class FormDataSerializer(serializers.ModelSerializer):
    """Serializer for form data"""
    #form_data  = serializers.StringRelatedField(many=False)
    
    class Meta:
        model = FormData
        fields = "__all__"