from django.db import models
import uuid

# Create your models here.
class Location(models.Model):  
    LEVEL_CHOICES = (
        (0, "Country"),
        (1, "Region"),
        (2, "District"),
        (3, "Ward"),
        (4, "Village"),
    )
        
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent        = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)
    name          = models.CharField(max_length = 150)
    level         = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES)
    iso3          = models.CharField(max_length=3, null=True, blank=True)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
    source        = models.CharField(max_length=20, null=True, blank=True, default="OHKR")
    active        = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True, null=True)
    updated_at    = models.DateTimeField(auto_now=True, null=True) 
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ohkr_locations'
        managed = True
        verbose_name = "Location"
        verbose_name_plural = "1. Locations"
        unique_together = ("source", "external_id", "level")  # safe uniqueness

        indexes = [
            models.Index(fields=["source", "external_id", "level"]),
            models.Index(fields=["parent", "level"]),
        ]

class Specie(models.Model):  
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length = 150)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
    source        = models.CharField(max_length=20, null=True, blank=True, default="OHKR")
    active        = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True, null=True)
    updated_at    = models.DateTimeField(auto_now=True, null=True) 
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ohkr_species'
        managed = True
        verbose_name = "Specie"
        verbose_name_plural = "2. Species"


class Disease(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length = 150)
    photo         = models.FileField(upload_to='assets/uploads/photo/', max_length=200, null=True, blank=True)
    description   = models.TextField(null=True, blank=True)
    causes        = models.TextField(null=True, blank=True)
    symptoms      = models.TextField(null=True, blank=True)
    diagnosis     = models.TextField(null=True, blank=True)
    treatment     = models.TextField(null=True, blank=True)
    prevention    = models.TextField(null=True, blank=True)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)  
    source        = models.CharField(max_length=20, null=True, blank=True, default="OHKR")
    active        = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True, null=True)
    updated_at    = models.DateTimeField(auto_now=True, null=True) 

    @property
    def last_updated(self):
        return self.updated_at.strftime("%Y%m%d%H%M%S")
    
    def __str__(self):
        return self.name

    
    class Meta:
        db_table = 'ohkr_diseases'
        managed = True
        verbose_name = "Disease"
        verbose_name_plural = "3. Diseases"


class Response(models.Model):  
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length = 150)
    description   = models.TextField(null=True, blank=True)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True, null=True)
    updated_at    = models.DateTimeField(auto_now=True, null=True) 

    @property
    def last_updated(self):
        return self.updated_at.strftime("%Y%m%d%H%M%S")
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ohkr_responses'
        managed = True
        verbose_name = "Response"
        verbose_name_plural = "5. Responses"


class ClinicalSign(models.Model):  
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length = 150)
    code          = models.CharField(max_length=10, null=True, blank=True)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
    source        = models.CharField(max_length=20, null=True, blank=True, default="OHKR")
    active        = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True, null=True)
    updated_at    = models.DateTimeField(auto_now=True, null=True) 

    @property
    def last_updated(self):
        return self.updated_at.strftime("%Y%m%d%H%M%S")
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ohkr_clinical_signs'
        managed = True
        verbose_name = "Clinical Sign"
        verbose_name_plural = "4. Clinical Signs"


class SpecieResponse(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    specie        = models.ForeignKey(Specie, on_delete=models.CASCADE)
    clinical_sign = models.ForeignKey(ClinicalSign, on_delete=models.SET_NULL, null=True)
    responses     = models.ManyToManyField(Response, null=True, blank=True)

    def __str__(self):
        return self.specie.name + " - " + self.clinical_sign.name

    class Meta:
        db_table = 'ohkr_specie_responses'
        managed = True
        verbose_name = "Specie Response"
        verbose_name_plural = "6. Specie Responses"


class ClinicalSignScore(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    disease       = models.ForeignKey(Disease, on_delete=models.CASCADE)
    clinical_sign = models.ForeignKey(ClinicalSign, on_delete=models.SET_NULL, null=True)
    score         = models.IntegerField()    

    def __str__(self):
        return self.disease.name

    class Meta:
        db_table = 'ohkr_scores'
        managed = True
        verbose_name = "Score"
        verbose_name_plural = "7. Scores"