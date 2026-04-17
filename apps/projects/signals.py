from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FormData
from .tasks import push_formdata_payload_task

@receiver(post_save, sender=FormData)
def push_data_on_create(sender, instance: FormData, created: bool, **kwargs):
    if instance.deleted == 1:
        return

    transaction.on_commit(lambda: push_formdata_payload_task.delay(instance.pk))
    
    

from .models import Project
from .utils import push_project_to_hub

@receiver(post_save, sender=Project)
def sync_public_project_with_hub(sender, instance, created, **kwargs):
    """
    Triggered whenever a Project is saved.
    Only pushes if the project is 'public' and active.
    """
    if instance.access == 'public' and instance.active:
        # For production, consider wrapping this in a Celery task 
        push_project_to_hub(instance)
        
        
        


# signals.py
# from .utils import find_incident_match

# # MATCHING LOGIC
# @receiver(post_save, sender=FormData)
# def auto_match_incident(sender, instance, created, **kwargs):
#     if created and not instance.parent_match:
#         match_uuid = find_incident_match(instance)
#         if match_uuid:
#             # Use .update() to avoid triggering post_save again (recursion)
#             FormData.objects.filter(pk=instance.pk).update(parent_match=match_uuid)