from django.db import transaction
from .models import Location


def upsert_location(payload: dict, *, level: int, parent=None, source="RDS", iso3=None, active=True):
    obj, created = Location.objects.update_or_create(
        source=source,
        level=level,
        external_id=payload.get("id"),
        defaults={
            "name": payload.get("name", "").strip(),
            "language_code": payload.get("language_code"),
            "parent": parent,
            "iso3": iso3 if level == 0 else None,
            "active": active,
        },
    )
    return obj, created


@transaction.atomic
def sync_locations(country_json: dict, *, source="RDS", active=True):
    created = updated = 0

    # Level 0: Country
    country, was_created = upsert_location(
        country_json,
        level=0,
        parent=None,
        source=source,
        iso3=country_json.get("iso3_code"),
        active=active,
    )
    created += was_created
    updated += not was_created

    # Level 1: Regions
    for region_json in country_json.get("administrative_level_1", []):
        region, was_created = upsert_location(
            region_json, level=1, parent=country, source=source, active=active
        )
        created += was_created
        updated += not was_created

        # Level 2: Districts
        for district_json in region_json.get("administrative_level_2", []):
            district, was_created = upsert_location(
                district_json, level=2, parent=region, source=source, active=active
            )
            created += was_created
            updated += not was_created

    return {"created": created, "updated": updated}
