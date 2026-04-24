import uuid
from django.db import models

# from django.contrib.gis.db import models  # Use GIS models

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractUser


from .qr_utils import generate_qr_string


class User(AbstractUser):
    # Override username field with no validators
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[],  # This removes all default restrictions
        help_text='Required. Any characters allowed.'
    )
    
    # You can add custom fields here if needed
    # bio = models.TextField(blank=True)
    # birth_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.username
    
    
# Create your models here.
class Tag(models.Model):
    """Model definition for tags"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)

    class Meta:
        """Meta definition for tags."""

        indexes = [models.Index(fields=["title"])]
        db_table = "ad_tags"
        managed = True
        app_label = "projects"
        verbose_name = "Tags"
        verbose_name_plural = "1. Tags"

    def __str__(self):
        return self.title


class Project(models.Model):
    """Model definition for project"""

    ACCESS_CHOICES = (
        ("private", "Private"),
        ("public", "Public"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(
        max_length=50, error_messages={"required": "Title is required"}
    )
    code = models.CharField(max_length=10, blank=True, null=True, unique=True)
    tags = models.ManyToManyField(Tag, blank=True)
    access = models.CharField(max_length=20, choices=ACCESS_CHOICES, default="private")
    auto_join = models.BooleanField(default=False)  # auto join the project
    accept_member = models.BooleanField(default=True)  # accept member
    accept_data = models.BooleanField(default=True)  # accept data or not
    active = models.BooleanField(default=True)  # active or not
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="p_created_by",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="p_updated_by",
        blank=True,
        null=True,
    )
    deleted = models.BooleanField(default=False)

    class Meta:
        """Meta definition for form definition."""

        indexes = [models.Index(fields=["title", "code"])]
        db_table = "ad_projects"
        managed = True
        app_label = "projects"
        verbose_name = "Project"
        verbose_name_plural = "2. Projects"

    def __str__(self):
        return self.title if self.title else self.pk


class ProjectMember(models.Model):
    """Model definition for project members"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, related_name="members", on_delete=models.CASCADE
    )
    member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    credibility_score = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta definition for form definition."""

        indexes = [models.Index(fields=["project", "member"])]
        db_table = "ad_project_members"
        managed = True
        app_label = "projects"
        verbose_name = "Project Member"
        verbose_name_plural = "3. Project Members"

    def __str__(self):
        return self.project.title


class FormDefinition(models.Model):
    """Model definition for form_definition"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, related_name="forms", on_delete=models.CASCADE)
    form_id = models.TextField(null=True, blank=True)
    depends_on = models.IntegerField(default=0)
    title = models.CharField(
        max_length=100, error_messages={"required": "Title is required"}
    )
    version = models.CharField(max_length=20, null=True, blank=True)
    short_title = models.CharField(max_length=10, null=True, blank=True)
    code = models.IntegerField(
        unique=True,
        null=True,
        error_messages={
            "required": "Code is required",
            "unique": "Code must be unique",
        },
    )
    form_type = models.TextField(null=True, blank=True)
    icon_type = models.CharField(
        max_length=50, null=True, blank=True, default="entypo:clipboard"
    )
    is_root = models.BooleanField(default=False)
    form_actions = models.CharField(max_length=255, blank=True, null=True)
    form_category = models.TextField(null=True, blank=True)
    xlsform = models.FileField(
        upload_to="jform/defn/",
        max_length=100,
        null=True,
        blank=True,
        error_messages={"required": "Xform is required"},
    )
    form_defn = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    short_description = models.CharField(max_length=100, null=True, blank=True)
    compulsory = models.IntegerField(default=0)
    children = models.CharField(max_length=100, null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    active = models.IntegerField(default=1)
    response = models.CharField(max_length=200, null=True, blank=True)
    callback_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="f_created_by",
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="f_updated_by",
        blank=True,
        null=True,
    )
    synced = models.IntegerField(default=0)

    @property
    def int_updated_at(self):
        return self.updated_at.strftime("%Y%m%d%H%M%S")

    class Meta:
        """Meta definition for form definition."""

        indexes = [models.Index(fields=["title", "code", "short_title"])]
        verbose_name = "Form definition"
        verbose_name_plural = "3. Form Definitions"
        db_table = "ad_form_definitions"

    def __str__(self):
        return self.title if self.title else self.pk


class FormAttachment(models.Model):
    "Model attachment for form definition"

    TYPE_CHOICES = (
        ("image", "image"),
        ("json", "json"),
        ("csv", "csv"),
        ("xls", "xls"),
        ("pdf", "pdf"),
    )

    form = models.ForeignKey(
        FormDefinition, related_name="attachments", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=150, blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="json")
    attachment = models.FileField(
        upload_to="uploads/form_attachments/", max_length=200, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta definition for form attachment."""

        indexes = [models.Index(fields=["title"])]
        verbose_name = "Form attachment"
        verbose_name_plural = "4. Form Attachments"
        db_table = "ad_form_attachments"

    def __str__(self):
        return self.title if self.title else self.pk


class FormData(models.Model):
    """Model definition for form_data"""

    uuid = models.TextField(max_length=100, blank=True, null=True)
    original_uuid = models.TextField(max_length=100, blank=True, null=True)

    parent_id = models.TextField(max_length=100, blank=True, null=True)
    form = models.ForeignKey(
        FormDefinition, related_name="form_data", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=150, blank=True, null=True)

    gps = models.CharField(max_length=150, blank=True, null=True)
    # gps = models.PointField(srid=4326, null=True, blank=True)
    path = models.TextField(blank=True, null=True)
    form_data = models.JSONField(null=False)

    parent_match = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
    score = models.IntegerField(default=1)

    photo = models.FileField(
        upload_to="uploads/", max_length=200, null=True, blank=True
    )
    deleted = models.IntegerField(default=0)
    created_at = models.DateTimeField(null=False)  # app created date
    updated_at = models.DateTimeField(auto_now=True)  # app updated date
    last_updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="fd_created_by", null=True
    )
    created_by_name = models.TextField(blank=True, null=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="fd_updated_by",
        blank=True,
        null=True,
    )
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="fd_last_updated_by",
        blank=True,
        null=True,
    )
    synced = models.IntegerField(default=0)

    push_status = models.BooleanField(default=False)
    response_id = models.TextField(max_length=200, blank=True, null=True)
    response_json = models.JSONField(null=True, blank=True)

    @property
    def int_updated_at(self):
        return self.updated_at.strftime("%Y%m%d%H%M%S")

    class Meta:
        """Meta definition for form data."""

        indexes = [models.Index(fields=["uuid", "form", "created_at"])]
        verbose_name = "Form data"
        verbose_name_plural = "4. Form data"
        db_table = "ad_form_data"

    def __str__(self):
        """Unicode representation of form data."""
        return self.uuid


class FormDataFile(models.Model):
    """File attachments linked to a form data record."""

    FILE_TYPE_CHOICES = (
        ("image", "Image"),
        ("video", "Video"),
        ("other", "Other"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form_data = models.ForeignKey(
        FormData,
        related_name="files",
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        upload_to="uploads/",
        max_length=200,
    )
    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        default="image",
    )
    original_name = models.CharField(max_length=255, blank=True, null=True)
    field_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="fd_files_uploaded_by",
        blank=True,
        null=True,
    )
    response_json = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["form_data", "created_at"])]
        verbose_name = "Form data file"
        verbose_name_plural = "5. Form Data Files"
        db_table = "ad_form_data_files"

    def __str__(self):
        return self.original_name or str(self.id)


class ProjectQRCode(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="qr_codes"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    issued_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    scan_count = models.IntegerField(default=0)  # Track scans

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def get_qr_string(self, request, user=None):
        """Generate encrypted QR string for this code"""
        join_url = (
            settings.CURRENT_INSTANCE_EXTERNAL_URL
            + "/api/v1/project/"
            + str(self.project.id)
            + "/join/"
        )

        expires_iso = self.expires_at.isoformat() if self.expires_at else ""
        return generate_qr_string(join_url, str(self.id), expires_iso)


class MatchingConfiguration(models.Model):
    """Stores the specific matching logic for a FormDefinition"""

    form_definition = models.OneToOneField(
        FormDefinition, on_delete=models.CASCADE, related_name="matching_config"
    )
    # Fields that MUST match exactly (e.g., ["species"])
    candidate_selection_fields = models.JSONField(default=list)
    # Max radius for candidate search in meters
    candidate_distance = models.FloatField(default=3000.0)
    # Time window for matching in hours
    time_window_hours = models.IntegerField(default=72)
    # Fields to calculate Jaccard similarity on (e.g., ["symptoms"])
    similarity_fields = models.JSONField(default=list)
    # Threshold to consider it the same incident (0.0 to 1.0)
    similarity_threshold = models.FloatField(default=0.7)

    def __str__(self):
        return f"Logic for {self.form_definition.title}"
