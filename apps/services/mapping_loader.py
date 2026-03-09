import json
from pathlib import Path
from django.conf import settings

MAPPING_FILE = (
    Path(settings.BASE_DIR) / "assets/mappings/community_report_mappings.json"
)

def load_mappings():
    with open(MAPPING_FILE, "r") as f:
        data = json.load(f)

    data["species"] = {k.lower(): v for k, v in data["species"].items()}
    data["regions"] = {k.lower(): v for k, v in data["regions"].items()}
    data["symptoms"] = {k.lower(): v for k, v in data["symptoms"].items()}

    return data

# Load mapping automatically
MAPPINGS = load_mappings()


def get_region_id(region_name):
    if not region_name:
        return None

    return MAPPINGS["regions"].get(region_name.lower().strip())


def get_species_id(species_name):
    if not species_name:
        return None

    return MAPPINGS["species"].get(species_name.lower().strip())


def get_symptom_id(symptom_name):
    if not symptom_name:
        return None

    return MAPPINGS["symptoms"].get(symptom_name.lower().strip())
