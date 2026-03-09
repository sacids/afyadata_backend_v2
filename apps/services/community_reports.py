from __future__ import annotations
import requests
from decouple import config
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from .mapping_loader import get_region_id, get_species_id, get_symptom_id


def _get(obj: Dict[str, Any], *keys, default=None):
    """Try multiple keys for the same value."""
    for k in keys:
        if k in obj and obj[k] not in (None, "", []):
            return obj[k]
    return default


def _parse_gps(gps_value: Any) -> Tuple[Optional[float], Optional[float]]:
    """
    Supports either:
    - {"latitude": ..., "longitude": ...}
    - "lat,long" string
    - None
    """
    if isinstance(gps_value, dict):
        lat = gps_value.get("latitude")
        lon = gps_value.get("longitude")
        return (
            float(lat) if lat is not None else None,
            float(lon) if lon is not None else None,
        )

    if isinstance(gps_value, str) and "," in gps_value:
        a, b = gps_value.split(",", 1)
        try:
            return float(a.strip()), float(b.strip())
        except ValueError:
            return None, None

    return None, None


def map_affected_animals(form_data: dict) -> list:
    """
    Maps local form_data to RDS affected_animals format.
    """
    species_id = form_data.get("aina_mfugo")
    clinical_signs = form_data.get("dalil_mfugo", [])
    quantity = form_data.get("idadi_dalili_wakubwa", 0)

    if not species_id:
        return []

    return [
        {
            "species_id": species_id,
            "quantity": int(quantity or 0),
            "clinical_signs": [{"clinical_sign_id": sign} for sign in clinical_signs],
        }
    ]


def build_payload(formdata) -> Dict[str, Any]:
    """
    Map FormData -> community report payload.
    Assumes relevant fields are in formdata.form_data JSON.
    """
    fd = formdata.form_data or {}
    gps = formdata.gps or {}

    species_id = get_species_id(fd.get("species"))
    region_id = get_region_id(fd.get("region"))
    symptoms = fd.get("symptoms", [])

    clinical_signs = [
        {"clinical_sign_id": get_symptom_id(s)} for s in symptoms if get_symptom_id(s)
    ]

    # location
    # try gps from JSONField, fallback to model.gps (string)
    lat, lon = _parse_gps(_get(gps, "gps", default=None))
    if (lat, lon) == (None, None):
        lat, lon = _parse_gps(getattr(formdata, "gps", None))

    # observation date: from JSONfield formdata
    obs_date = _get(fd, "observation_date", "observationDate")
    if not obs_date:
        # submitted_at in your model is app created date; ensure it's ISO 8601 UTC
        dt = getattr(formdata, "submitted_at", None) or datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        obs_date = dt.isoformat().replace("+00:00", "Z")

    # create a payload
    payload: Dict[str, Any] = {
        "country_id": "562daed1-de99-44de-8222-81b59acead98",
        "administrative_region_id": region_id,
        "latitude": lat,
        "longitude": lat,
        "observation_date": obs_date,
        "reporter_comment": _get(
            fd, "comment", "reporterComment", default="Community report comment."
        ),
        "reporter_role": "Field reporter",
        "external_id": "AFYADATA-6890",
        "application_id": "afb2923b-60d8-4a03-af7e-f4e93ce22df2",
        "description": fd.get(
            "description",
            "A dedicated form to collect animal clinical signs at the community level",
        ),
        "affected_animals": [
            {
                "species_id": species_id,
                "quantity": fd.get("quantity", 0),
                "clinical_signs": clinical_signs,
            }
        ],
    }

    return payload


def push_data(*, callback_url: str, payload: dict) -> dict:
    resp = requests.post(
        callback_url,
        json=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json() if resp.content else {"ok": True}
