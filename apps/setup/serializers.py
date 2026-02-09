# serializers.py
from rest_framework import serializers
from .models import Language, LanguageVersion, LanguageDownload
from django.contrib.auth.models import User

class LanguageSerializer(serializers.ModelSerializer):
    download_count = serializers.SerializerMethodField()
    latest_version = serializers.SerializerMethodField()
    
    class Meta:
        model = Language
        fields = ['code', 'name', 'native_name', 'is_active', 'is_default', 
                 'created_at', 'download_count', 'latest_version']
        read_only_fields = ['created_at', 'download_count', 'latest_version']
    
    def get_download_count(self, obj):
        return LanguageDownload.objects.filter(language=obj).count()
    
    def get_latest_version(self, obj):
        latest = obj.versions.filter(is_published=True).order_by('-created_at').first()
        if latest:
            return latest.version
        return None

class LanguageVersionSerializer(serializers.ModelSerializer):
    language_name = serializers.CharField(source='language.name', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = LanguageVersion
        fields = ['id', 'language', 'language_name', 'language_code', 'version', 
                 'file_size', 'file_hash', 'is_published', 'created_by', 
                 'created_by_name', 'created_at', 'published_at']
        read_only_fields = ['file_size', 'file_hash', 'created_at', 'published_at']
    
    def validate_file(self, value):
        """Validate uploaded language file"""
        # Check file extension
        if not value.name.endswith('.json'):
            raise serializers.ValidationError("Only JSON files are allowed")
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(f"File too large. Max size is {max_size/1024/1024}MB")
        
        # Validate JSON structure
        try:
            content = value.read().decode('utf-8')
            data = json.loads(content)
            
            # Check for required config section
            if 'config' not in data:
                raise serializers.ValidationError("Language file must contain 'config' section")
            
            # Check config fields
            config = data['config']
            if 'code' not in config:
                raise serializers.ValidationError("Config section must contain 'code' field")
            
            # Validate language code matches filename
            expected_code = value.name.replace('.json', '').lower()
            if config['code'].lower() != expected_code:
                raise serializers.ValidationError(
                    f"Language code in config ({config['code']}) doesn't match filename ({expected_code})"
                )
            
            # Reset file pointer
            value.seek(0)
            
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON file")
        
        return value

class LanguageUploadSerializer(serializers.Serializer):
    """Serializer for language file upload"""
    file = serializers.FileField()
    version = serializers.CharField(max_length=20)
    publish = serializers.BooleanField(default=False)
    
    def validate(self, data):
        # Additional validation can be done here
        return data

class LanguageDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageDownload
        fields = ['language', 'version', 'device_id', 'app_version']
        read_only_fields = ['downloaded_at', 'ip_address']

class LanguageStatsSerializer(serializers.Serializer):
    """Serializer for language statistics"""
    code = serializers.CharField()
    name = serializers.CharField()
    native_name = serializers.CharField()
    download_count = serializers.IntegerField()
    latest_version = serializers.CharField()
    file_size = serializers.IntegerField()