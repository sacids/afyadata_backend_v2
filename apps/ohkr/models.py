from django.db import models
import uuid

# Create your models here.
class Specie(models.Model):  
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length = 150)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
    
    def __str__(self):
        return self.title

    class Meta:
        db_table = 'ohkr_species'
        managed = True
        
class Disease(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length = 150)
    description   = models.TextField(null=True, blank=True)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
    
    #image
    #description    
    
    def __str__(self):
        return self.title

    
    class Meta:
        db_table = 'ohkr_diseases'
        managed = True


class ClinicalSign(models.Model):  
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length = 150)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
    
    def __str__(self):
        return self.title

    class Meta:
        db_table = 'ohkr_clinical_signs'
        managed = True

class ClinicalSignScore(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    disease       = models.ForeignKey(Disease, on_delete=models.CASCADE)
    clinical_sign = models.ForeignKey(ClinicalSign, on_delete=models.CASCADE)
    score         = models.IntegerField()    

    def __str__(self):
        return self.disease.title+' : '+self.symptom.title

    class Meta:
        db_table = 'ohkr_scores'
        managed = True