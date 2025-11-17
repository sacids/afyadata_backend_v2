from django.contrib.auth.models import User, Group
from .models import *
from rest_framework import serializers


class SpecieSerializer(serializers.ModelSerializer):
    """Serializer for specie"""
    class Meta:
        model = Specie
        fields = '__all__'


class DiseaseSerializer(serializers.ModelSerializer):
    """Serializer for disease"""
    class Meta:
        model = Disease
        fields = '__all__'

class ClinicalResponseSerializer(serializers.ModelSerializer):
    """Serializer for clinical response"""
    class Meta:
        model = ClinicalResponse
        fields = '__all__'

class ClinicalSignSerializer(serializers.ModelSerializer):
    """Serializer for clinical sign"""
    responses = ClinicalResponseSerializer(many=True)

    class Meta:
        model = ClinicalSign
        fields = '__all__'


class ScoreSerializer(serializers.ModelSerializer):
    """Serializer for clinical sign score"""
    class Meta:
        model = ClinicalSignScore
        fields = '__all__'
