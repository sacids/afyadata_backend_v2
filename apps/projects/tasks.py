from celery import shared_task
import logging

from apps.projects.models import FormData, FormDataFile, ProjectMember
from apps.projects.utils import save_uploaded_file_snapshots
from apps.esb.utils import build_payload, push_payload
from apps.ohkr.ohkr_service import OHKRService
from apps.ohkr.models import ReferenceData, OHKRDetectedDisease
from apps.services.messaging import MessagingService
from .utils import get_permitted_users_for_created_by

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

        if member.credibility_score < 50:
            logger.info(
                "Skipping FAO push for formdata %s: credibility score %s is less than 50.",
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



@shared_task
def predict_disease_task(formdata_id):
    try:
        form_data = FormData.objects.get(pk=formdata_id)
        payload = form_data.form_data or {} # submitted form data as json
        created_by = form_data.created_by # user submitted data
        form_id = form_data.form.pk

        species_name = payload.get("species")
        symptoms = payload.get("symptoms", [])

        if not species_name:
            return f"No species found for FormData {formdata_id}"

        if not symptoms:
            return f"No symptoms found for FormData {formdata_id}"

        specie = (
            ReferenceData.objects.filter(
                rd_type="specie",
                name__iexact=species_name,
                active=True,
            )
            .first()
        )

        if not specie:
            return f"Specie '{species_name}' not found"

        result = OHKRService.predict_disease(
            specie_id=specie.id,
            clinical_sign_codes=symptoms,
        )

        # TODO: Handle the result - save to DB, send SMS, etc. => top 3 diseases with score
        if result.get("status") == True:
            diseases = result.get("data", [])
            # 1. Save to ohkr predicted disease model
            for disease in diseases:
                logger.info(f"Saving detected disease {disease['title']} with score {disease['score']} for FormData {formdata_id}")
                # Save to DB
                OHKRDetectedDisease.objects.create(
                    form_data=form_data,
                    disease_id=disease["disease_id"],
                    location=payload.get("location", "unknown"),
                    score=disease["score"],
                )

            # 2. Send SMS to CAW - TODO: integrate with SMS service and CAW contact info
            messaging_service = MessagingService()
            name = created_by.get_full_name()
            phone = created_by.profile.phone if hasattr(created_by, "profile") else "unknown"
            disease_list = ", ".join([f"{d['title']} (score: {d['score']})" for d in diseases])

            #recipients
            recipients = get_permitted_users_for_created_by(form_id, created_by.pk)

            if recipients:
                for recipient in recipients:
                    #name 
                    recipient_name = recipient.get_full_name()
                    #phone
                    recipient_phone = recipient.profile.phone if hasattr(recipient, "profile") else "unknown"

                    if recipient_phone != "unknown":
                        personalized_message = f"Cher {recipient_name}, le système a identifié la ou les maladies suivantes {disease_list} à partir des signes cliniques soumis par {name} {phone} avec le formulaire ID {form_data.id}. Veuillez examiner les signes cliniques dans AfyaData et investiguer le cas dans son site (localisation). Merci."
                        messaging_service.send_sms(recipient_phone, personalized_message)
                    else:
                        logger.warning(f"Recipient {recipient.pk} does not have a phone number. Skipping SMS notification.")
            
        return result

    except FormData.DoesNotExist:
        return f"FormData {formdata_id} does not exist"

    except Exception as e:
        return str(e)