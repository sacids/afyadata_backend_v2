import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FormData
from apps.esb.utils import build_payload, push_payload

@receiver(post_save, sender=FormData)
def push_data_on_create(sender, instance: FormData, created: bool, **kwargs):
    if instance.deleted == 1:
        return

    # load payload configs
    configs = instance.form.payload_configs.filter(is_active=True)

    def do_push():
        # reload fresh instance (avoid stale state)
        fd = FormData.objects.get(pk=instance.pk)
        push_status = fd.push_status

        logging.info("== Form data ==")
        logging.info(fd)

        for cfg in configs:
            # prevent re-send if already sent
            if push_status is True:
                continue
            
            # build payload
            payload = build_payload(fd, cfg)
            logging.info("== API Payload ==")
            logging.info(payload)

            # push data to the server
            ok, info = push_payload(cfg, payload)

        # update status to avoid deplicate
        FormData.objects.filter(pk=fd.pk).update(push_status=True)
    transaction.on_commit(do_push)