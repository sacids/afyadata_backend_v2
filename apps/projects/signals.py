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
