from celery import shared_task
import logging

from apps.projects.models import FormData, FormDataFile
from apps.projects.utils import save_uploaded_file_snapshots
from apps.esb.utils import build_payload, push_payload


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def save_formdata_files_task(self, formdata_id, file_snapshots, uploaded_by_id=None):
    saved_files = save_uploaded_file_snapshots(
        file_snapshots,
        upload_subdir="assets/uploads/",
    )

    formdata = FormData.objects.get(pk=formdata_id)

    file_objects = [
        FormDataFile(
            form_data=formdata,
            file=item["path"],
            file_type=item["file_type"],
            original_name=item["original_name"],
            field_name=item["field_name"],
            uploaded_by_id=uploaded_by_id,
        )
        for item in saved_files
    ]
    if file_objects:
        FormDataFile.objects.bulk_create(file_objects)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def push_formdata_payload_task(self, formdata_id):
    formdata = FormData.objects.select_related("form").get(pk=formdata_id)

    if formdata.deleted == 1 or formdata.push_status is True:
        return

    configs = formdata.form.payload_configs.filter(is_active=True).prefetch_related(
        "field_maps",
        "value_mappings",
    )

    for config in configs:
        if formdata.push_status is True:
            break

        payload = build_payload(formdata, config)
        logging.info("== API PAYLOAD ==")
        logging.info(payload)

        # Push data
        push_payload(config, payload, formdata=formdata)
        formdata.refresh_from_db(fields=["push_status"])
