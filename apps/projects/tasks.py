from celery import shared_task

from apps.projects.models import FormData
from apps.projects.utils import save_uploaded_file_snapshots


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def save_formdata_files_task(self, formdata_id, file_snapshots):
    saved_paths = save_uploaded_file_snapshots(
        file_snapshots,
        upload_subdir="assets/uploads/photos/",
    )

    first_saved_path = next(
        (path for paths in saved_paths.values() for path in paths if path),
        None,
    )

    if first_saved_path:
        FormData.objects.filter(pk=formdata_id).update(photo=first_saved_path)
