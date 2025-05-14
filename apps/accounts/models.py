
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """model for profile"""
    user             = models.OneToOneField(User, on_delete=models.CASCADE)
    digest           = models.CharField(max_length=200,null=True)
    pic              = models.ImageField(upload_to="uploads/", blank=True, null=True)
    phone            = models.CharField(max_length=20, blank=True, null=True)
    verified_by        = models.ForeignKey(User, null=True, blank=True, on_delete = models.SET_NULL, related_name="verified_by")
    verified_at        = models.DateTimeField(null=True, blank=True) 
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True) 


    class Meta:
        db_table = 'ad_profile'
        managed = True

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)


    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()
