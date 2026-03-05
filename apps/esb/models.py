from django.db import models
from apps.projects.models import FormDefinition
import uuid


# Create your models here.
class FormPayloadConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        FormDefinition, on_delete=models.CASCADE, related_name="payload_configs"
    )
    endpoint = models.URLField(blank=True, null=True)  # where to POST
    method = models.CharField(max_length=10, default="POST")
    headers = models.JSONField(
        default=dict, blank=True
    )  # optional (Accept, Content-Type...)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "esb_form_payload_config"
        managed = True
        verbose_name = "FormPayloadConfig"
        verbose_name_plural = "1. FormPayloadConfig"

    def __str__(self):
        return f"{self.form.title}"


class FormPayloadFieldMap(models.Model):
    TRANSFORM_CHOICES = (
        ("lower", "toLower"),
        ("upper", "toUpper"),
        ("to_uuid", "toUuid"),
        ("to_int", "toInt"),
        ("to_float", "toFloat"),
        ("iso_datetime", "isoDatetime"),
        ("gps_lat", "latitude"),
        ("gps_lng", "longitude"),
        ("map:administrative_region", "map:administrative_region"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(
        FormPayloadConfig, on_delete=models.CASCADE, related_name="field_maps"
    )
    payload_field = models.CharField(max_length=120)

    # JSON path/key in form_data, e.g. "country_id" or "meta.country" or "animal[0].species"
    form_data_path = models.CharField(max_length=200, blank=True, null=True)

    # default if not found
    default_value = models.CharField(max_length=255, blank=True, null=True)

    # required field?
    required = models.BooleanField(default=False)

    # optional transformation hint
    transform = models.CharField(
        max_length=50, choices=TRANSFORM_CHOICES, blank=True, null=True
    )

    class Meta:
        db_table = "esb_form_payload_field_map"
        managed = True
        verbose_name = "FormPayloadFieldMap"
        verbose_name_plural = "2. FormPayloadFieldMap"
        unique_together = ("config", "payload_field")
        indexes = [models.Index(fields=["payload_field"])]

    def __str__(self):
        return f"{self.payload_field} <- {self.form_data_path}"


class FormValueMapping(models.Model):
    """Form value mapping"""
    ENTITY_CHOICES = (
        ("administrative_region", "Administrative Region"),
        ("species", "Species"),
        ("symptom", "Symptom"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(FormPayloadConfig, on_delete=models.CASCADE, related_name="value_mappings")
    entity_type = models.CharField(max_length=50, choices=ENTITY_CHOICES)
    source_value = models.CharField(max_length=200)
    target_value = models.CharField(max_length=200)

    class Meta:
        db_table = "esb_form_value_mapping"
        managed = True
        verbose_name = "FormValueMapping"
        verbose_name_plural = "3. FormValueMapping"
        unique_together = ("config", "entity_type", "source_value")
        indexes = [models.Index(fields=["config", "entity_type", "source_value"])]

    def save(self, *args, **kwargs):
        if self.source_value:
            self.source_value = self.source_value.strip().lower()
        super().save(*args, **kwargs)