from celery import shared_task
import logging

from apps.projects.models import FormData, FormDataFile, ProjectMember
from apps.projects.utils import save_uploaded_file_snapshots
from apps.esb.utils import build_payload, push_payload

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def save_formdata_files_task(self, formdata_id, file_snapshots, uploaded_by_id=None):
    saved_files = save_uploaded_file_snapshots(
        file_snapshots,
        upload_subdir="uploads/",
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
    formdata = FormData.objects.select_related("form", "form__project", "created_by").get(pk=formdata_id)

    if formdata.deleted == 1 or formdata.push_status is True:
        return

    if formdata.created_by_id:
        member = (
            ProjectMember.objects.filter(
                project=formdata.form.project,
                member_id=formdata.created_by_id,
                active=True,
            )
            .only("credibility_score")
            .first()
        )

        if not member:
            logger.info(
                "Skipping FAO push for formdata %s: creator is not an active member of project %s.",
                formdata.pk,
                formdata.form.project_id,
            )
            return

        if member.credibility_score <= 50:
            logger.info(
                "Skipping FAO push for formdata %s: credibility score %s is not greater than 50.",
                formdata.pk,
                member.credibility_score,
            )
            return
    else:
        logger.info(
            "Skipping FAO push for formdata %s: no created_by user is attached to the submission.",
            formdata.pk,
        )
        return

    configs = formdata.form.payload_configs.filter(is_active=True).prefetch_related(
        "field_maps",
        "value_mappings",
    )

    for config in configs:
        if formdata.push_status is True:
            break

        payload = build_payload(formdata, config)
        push_payload(config, payload, formdata=formdata)
        formdata.refresh_from_db(fields=["push_status"])
