import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

# Create your models here.
class Tag(models.Model):
    """Model definition for tags"""
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title    = models.CharField(max_length=50)
    
    class Meta:
        """Meta definition for tags."""
        indexes = [
            models.Index(fields=['title'])
        ]
        db_table    = 'ad_tags'
        managed     = True
        app_label   = 'projects'
        verbose_name = "Tags"
        verbose_name_plural = "1. Tags"
    
    def __str__(self):
        return self.title


class Project(models.Model):
    """Model definition for project"""
    ACCESS_CHOICES = (
        ('private', 'Private'),
        ('public', 'Public'),
    )

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title           = models.CharField(max_length=50)
    code            = models.CharField(max_length=50, blank=True, null=True, unique=True)
    tags            = models.ManyToManyField(Tag, null=True, blank=True)
    access          = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='private')
    auto_join       = models.BooleanField(default=False)
    accept_member   = models.BooleanField(default=True) # accept member
    accept_data     = models.BooleanField(default=True) # accept data or not
    active          = models.BooleanField(default=True) # active or not
    description     = models.TextField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True) 
    created_by      = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='p_created_by', blank=True, null=True)
    updated_by      = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='p_updated_by', blank=True, null=True)
    
    class Meta:
        """Meta definition for form definition."""
        indexes = [
            models.Index(fields=['title', 'code'])
        ]
        db_table    = 'ad_projects'
        managed     = True
        app_label   = 'projects'
        verbose_name = "Project"
        verbose_name_plural = "2. Projects"
    
    def __str__(self):
        return self.title if self.title else self.pk
    

class ProjectMember(models.Model):
    """Model definition for project members"""
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project         = models.ForeignKey(Project, related_name='members', on_delete=models.CASCADE)
    member          = models.ForeignKey(User, on_delete=models.CASCADE)
    active          = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True) 
    
    class Meta:
        """Meta definition for form definition."""
        indexes = [
            models.Index(fields=['project', 'member'])
        ]
        db_table    = 'ad_project_members'
        managed     = True
        app_label   = 'projects'
        verbose_name = "Project Member"
        verbose_name_plural = "3. Project Members"

    def __str__(self):
        return self.project.title
    

class FormDefinition(models.Model):
    """Model definition for form_definition"""
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project       = models.ForeignKey(Project, related_name='forms', on_delete=models.CASCADE)
    title         = models.CharField(max_length=100)
    short_title   = models.CharField(max_length=10, null=True, blank=True)
    short_description  = models.CharField(max_length=100, null=True, blank=True)
    description   = models.TextField(null=True, blank=True)
    version       = models.CharField(max_length=20, null=True, blank=True)
    code          = models.IntegerField(unique=True, null=True)
    sort_order    = models.IntegerField(default=0)
    xlsform       = models.FileField(upload_to='jform/defn/', max_length=100, null=True, blank=True)
    form_actions  = models.CharField(max_length=255, blank=True, null=True)
    form_defn     = models.TextField(null=True,blank=True)
    children      = models.CharField(max_length=100,null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True) 
    created_by    = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='f_created_by', blank=True, null=True)
    updated_by    = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='f_updated_by', blank=True, null=True)
    synced        = models.IntegerField(default=0)
    @property
    def int_updated_at(self):
        return self.updated_at.strftime("%Y%m%d%H%M%S")

    class Meta:
        """Meta definition for form definition."""
        indexes = [
            models.Index(fields=['title', 'code', 'short_title'])
        ]
        verbose_name = 'Form definition'
        verbose_name_plural = '3. Form Definitions'
        db_table = 'ad_form_definitions'

    def __str__(self):
        return self.title if self.title else self.pk
    
class FormData(models.Model):
    """Model definition for form_data"""
    uuid          = models.TextField(max_length=100, blank=True, null=True)
    original_uuid = models.TextField(max_length=100, blank=True, null=True)
    parent_id     = models.TextField(max_length=100, blank=True, null=True)
    form          = models.ForeignKey(FormDefinition, related_name="form_data", on_delete=models.CASCADE)
    title         = models.CharField(max_length=150, blank=True, null=True)
    gps           = models.CharField(max_length=150, blank=True, null=True)
    path          = models.TextField(blank=True, null=True)
    form_data     = models.JSONField(null=False)
    deleted       = models.IntegerField(default=0)
    created_at    = models.DateTimeField(null=False) # app created date
    updated_at    = models.DateTimeField(auto_now=True) # app updated date
    last_updated_at = models.DateTimeField(auto_now=True)
    submitted_at    = models.DateTimeField(auto_now_add=True)
    created_by      = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='fd_created_by', null=True)
    created_by_name = models.TextField(blank=True, null=True)
    updated_by      = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='fd_updated_by', blank=True, null=True)  
    last_updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='fd_last_updated_by', blank=True, null=True)  
    synced          = models.IntegerField(default=0) 
    
    @property
    def int_updated_at(self):
        return self.updated_at.strftime("%Y%m%d%H%M%S")

    class Meta:
        """Meta definition for form data."""
        indexes = [
            models.Index(fields=['uuid',  'form', 'created_at'])
        ]
        verbose_name = 'Form data'
        verbose_name_plural = '4. Form data'
        db_table = 'ad_form_data'

    def __str__(self):
        """Unicode representation of form data."""
        return self.uuid