from django.db import models

# Create your models here.
# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import hashlib
import os


class Language(models.Model):
    """Available languages in the system"""

    code = models.CharField(
        max_length=10, unique=True, primary_key=True
    )  # 'en', 'fr', 'sw', etc.
    name = models.CharField(max_length=100)  # 'English', 'French'
    native_name = models.CharField(max_length=100)  # 'English', 'Français'
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ["name"]
        verbose_name = "Language"
        verbose_name_plural = "Languages"


class LanguageVersion(models.Model):
    """Versioned language translations"""

    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.CharField(max_length=20)  # e.g., '1.0.0', '1.1.0'
    file = models.FileField(upload_to="language_files/%Y/%m/%d/")
    file_size = models.IntegerField()  # Size in bytes
    file_hash = models.CharField(max_length=64)  # SHA256 hash for integrity check
    translations = models.JSONField(default=dict)  # Store the actual JSON content
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.language.code} v{self.version}"

    def save(self, *args, **kwargs):
        # Calculate file size and hash
        if self.file:
            self.file_size = self.file.size
            self.file_hash = self.calculate_file_hash()

            # Read and store JSON content
            self.file.seek(0)
            content = self.file.read().decode("utf-8")
            self.translations = json.loads(content)

        # Set published_at if publishing
        if self.is_published and not self.pk:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def calculate_file_hash(self):
        """Calculate SHA256 hash of file content"""
        self.file.seek(0)
        file_hash = hashlib.sha256()
        for chunk in self.file.chunks():
            file_hash.update(chunk)
        return file_hash.hexdigest()

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["language", "version"]
        verbose_name = "Language Version"
        verbose_name_plural = "Language Versions"


class LanguageDownload(models.Model):
    """Track language downloads for analytics"""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    version = models.ForeignKey(LanguageVersion, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255, blank=True)  # For anonymous tracking
    app_version = models.CharField(max_length=20, blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-downloaded_at"]
        verbose_name = "Language Download"
        verbose_name_plural = "Language Downloads"
