
from django.db import models, connection
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth import get_user_model
User = get_user_model()


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

    @staticmethod
    def table_exists():
        """Guard profile signal usage during partial first-boot migrations."""
        return Profile._meta.db_table in connection.introspection.table_names()

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        """Create profile for user if it doesn't exist"""
        if not Profile.table_exists():
            return
        if created:
            Profile.objects.get_or_create(user=instance)
        else:
            # Ensure profile exists even if user wasn't just created
            Profile.objects.get_or_create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        """Save the user's profile"""
        if not Profile.table_exists():
            return
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            # Create if it doesn't exist
            Profile.objects.create(user=instance)
