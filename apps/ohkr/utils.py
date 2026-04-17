from django.db import transaction

from apps.projects.models import FormDefinition

from .models import Location, ReferenceData


LOCATION_RD_TYPE_BY_LEVEL = {
    0: "administrative_level_0",
    1: "administrative_level_1",
    2: "administrative_level_2",
}


def resolve_reference_form(form):
    if isinstance(form, FormDefinition):
        return form
    return FormDefinition.objects.get(pk=form)


def upsert_reference_item(
    payload: dict,
    *,
    form,
    rd_type: str,
    source="RDS",
    active=True,
    code_key=None,
    external_id_key="id",
    name_key="name",
):
    form = resolve_reference_form(form)
    name = (payload.get(name_key) or "").strip()
    external_id = payload.get(external_id_key)
    code = payload.get(code_key) if code_key else None

    lookup = {
        "form": form,
        "rd_type": rd_type,
        "source": source,
    }
    if external_id:
        lookup["external_id"] = external_id
    else:
        lookup["name"] = name

    obj, created = ReferenceData.objects.update_or_create(
        **lookup,
        defaults={
            "name": name,
            "code": code,
            "language_code": payload.get("language_code"),
            "active": active,
        },
    )
    return obj, created


def upsert_location_legacy(
    payload: dict, *, level: int, parent=None, source="RDS", iso3=None, active=True
):
    obj, created = Location.objects.update_or_create(
        source=source,
        level=level,
        external_id=payload.get("id"),
        defaults={
            "name": (payload.get("name") or "").strip(),
            "language_code": payload.get("language_code"),
            "parent": parent,
            "iso3": iso3 if level == 0 else None,
            "active": active,
        },
    )
    return obj, created


@transaction.atomic
def sync_locations(country_json: dict, *, source="RDS", active=True, form=None):
    created = updated = 0

    if form:
        for level, rd_type in LOCATION_RD_TYPE_BY_LEVEL.items():
            payloads = []
            if level == 0:
                payloads = [country_json]
            elif level == 1:
                payloads = country_json.get("administrative_level_1", [])
            elif level == 2:
                for region_json in country_json.get("administrative_level_1", []):
                    payloads.extend(region_json.get("administrative_level_2", []))

            for payload in payloads:
                _, was_created = upsert_reference_item(
                    payload,
                    form=form,
                    rd_type=rd_type,
                    source=source,
                    active=active,
                )
                created += was_created
                updated += not was_created

        return {"created": created, "updated": updated}

    country, was_created = upsert_location_legacy(
        country_json,
        level=0,
        parent=None,
        source=source,
        iso3="TZA",
        active=active,
    )
    created += was_created
    updated += not was_created

    for region_json in country_json.get("administrative_level_1", []):
        region, was_created = upsert_location_legacy(
            region_json, level=1, parent=country, source=source, active=active
        )
        created += was_created
        updated += not was_created

        for district_json in region_json.get("administrative_level_2", []):
            _, was_created = upsert_location_legacy(
                district_json, level=2, parent=region, source=source, active=active
            )
            created += was_created
            updated += not was_created

    return {"created": created, "updated": updated}


@transaction.atomic
def sync_reference_values(
    values,
    *,
    form,
    rd_type: str,
    source="RDS",
    active=True,
    code_key=None,
    external_id_key="id",
    name_key="name",
):
    created = updated = 0

    for item in values:
        _, was_created = upsert_reference_item(
            item,
            form=form,
            rd_type=rd_type,
            source=source,
            active=active,
            code_key=code_key,
            external_id_key=external_id_key,
            name_key=name_key,
        )
        created += was_created
        updated += not was_created

    return {"created": created, "updated": updated}
