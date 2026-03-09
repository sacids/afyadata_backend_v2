from django.db import models
import uuid

# Create your models here.
class Specie(models.Model):  
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length = 150)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
    active        = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True, null=True)
    updated_at    = models.DateTimeField(auto_now=True, null=True) 
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ohkr_species'
        managed = True
        verbose_name = "Specie"
        verbose_name_plural = "1. Species"
        
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
        verbose_name_plural = "2. Diseases"

class ClinicalResponse(models.Model):  
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
        verbose_name_plural = "3. Responses"

class ClinicalSign(models.Model):  
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name          = models.CharField(max_length = 150)
    code          = models.CharField(max_length=10, null=True, blank=True)
    external_id   = models.CharField(max_length = 150, null=True, blank=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True)
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
    clinical_sign = models.ForeignKey(ClinicalSign, on_delete=models.CASCADE)
    responses     = models.ManyToManyField(ClinicalResponse, null=True, blank=True)

    def __str__(self):
        return self.specie.name + " - " + self.clinical_sign.name

    class Meta:
        db_table = 'ohkr_specie_responses'
        managed = True
        verbose_name = "Specie Response"
        verbose_name_plural = "5. Specie Responses"

class ClinicalSignScore(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    disease       = models.ForeignKey(Disease, on_delete=models.CASCADE)
    clinical_sign = models.ForeignKey(ClinicalSign, on_delete=models.CASCADE)
    score         = models.IntegerField()    

    def __str__(self):
        return self.disease.name

    class Meta:
        db_table = 'ohkr_scores'
        managed = True
        verbose_name = "Score"
        verbose_name_plural = "6. Scores"
        
        
        
        
        


class FirstAidAction(models.Model):
    """Reusable snippets of advice or specific physical tasks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, help_text="e.g., USE_GLOVES")
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.IntegerField(default=1, help_text="Higher numbers (e.g., 10) show at the top")
    
    # Category helps group actions in the UI (e.g., Safety, Treatment, Referral)
    CATEGORY_CHOICES = [
        ('safety', 'Personal Safety'),
        ('care', 'Immediate Care'),
        ('referral', 'Referral/Urgent'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='care')
    
    def __str__(self):
        return f"[{self.category.upper()}] {self.title}"

    class Meta:
        ordering = ['-priority']

class FirstAidRule(models.Model):
    """The logic engine: matches conditions to a set of actions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="e.g., Fever in Cattle Rule")
    
    # Criteria
    species = models.ManyToManyField('Specie', blank=True)
    clinical_signs = models.ManyToManyField('ClinicalSign', blank=True)
    
    # Age constraints (optional)
    min_age_months = models.IntegerField(null=True, blank=True)
    max_age_months = models.IntegerField(null=True, blank=True)
    
    # Outcomes
    actions = models.ManyToManyField(FirstAidAction, related_name="rules")
    
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name