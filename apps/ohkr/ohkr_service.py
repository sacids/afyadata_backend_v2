from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from .models import Disease, ReferenceData, OHKRScore


class OHKRService:
    def format_data_request(submitted_data):
        """
        Convert submitted form data into payload required by predict_disease()
        """

        species_name = submitted_data.get("species")
        symptoms = submitted_data.get("symptoms", [])

        specie = ReferenceData.objects.filter(
            rd_type="specie",
            name__iexact=species_name
        ).first()

        if not specie:
            raise ValueError(f"Specie '{species_name}' not found")

        return {
            "specie_id": str(specie.id),
            "clinical_signs": symptoms,
        }
    
    @staticmethod
    def predict_disease(specie_id, clinical_sign_codes):
        if not specie_id:
            raise ValidationError({"specie_id": "Specie ID is required"})

        if not clinical_sign_codes:
            raise ValidationError({"clinical_signs": "Clinical signs are required"})

        specie = ReferenceData.objects.filter(
            id=specie_id,
            rd_type="specie",
            active=True
        ).first()

        if not specie:
            return {
                "status": False,
                "data": "Invalid or inactive specie"
            }

        clinical_signs = ReferenceData.objects.filter(
            code__in=clinical_sign_codes,
            rd_type="clinical_sign",
            active=True
        )

        clinical_sign_ids = list(clinical_signs.values_list("id", flat=True))

        if not clinical_sign_ids:
            return {
                "status": False,
                "data": "No matching clinical signs found"
            }

        disease_total_scores = (
            OHKRScore.objects
            .filter(specie=specie)
            .values("disease_id")
            .annotate(total_score=Sum("score"))
        )

        disease_total_map = {
            item["disease_id"]: item["total_score"]
            for item in disease_total_scores
        }

        if not disease_total_map:
            return {
                "status": False,
                "data": "No disease score mapping found for this specie"
            }

        matched_scores = (
            OHKRScore.objects
            .filter(
                specie=specie,
                clinical_sign_id__in=clinical_sign_ids,
                disease_id__in=disease_total_map.keys()
            )
            .values("disease_id")
            .annotate(matched_score=Sum("score"))
            .order_by("-matched_score")
        )

        if not matched_scores:
            return {
                "status": False,
                "data": "No match found"
            }

        disease_map = {
            disease.id: disease.name
            for disease in Disease.objects.filter(id__in=disease_total_map.keys())
        }

        results = []

        for item in matched_scores:
            disease_id = item["disease_id"]
            total_score = disease_total_map.get(disease_id, 0)

            if total_score == 0:
                continue

            percentage = (item["matched_score"] / total_score) * 100

            results.append({
                "disease_id": str(disease_id),
                "title": disease_map.get(disease_id, "Unknown disease"),
                "score": round(percentage, 2)
            })

        return {
            "status": True,
            "data": results
        }