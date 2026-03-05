import re
import requests
from django.utils import timezone
from datetime import datetime, timezone
from .models import *


def get_from_dict_path(d: dict, path: str):
    cur = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def get_value(fd, path: str):
    """
    Supported:
      - model.gps
      - model.created_at
      - form_data.latitude
      - form_data.location.lat
    """
    if not path:
        return None

    root, _, rest = path.partition(".")
    if root == "model":
        return getattr(fd, rest, None)

    if root == "form_data":
        data = fd.form_data or {}
        return get_from_dict_path(data, rest) if rest else data

    # allow direct "gps" meaning form_data.gps (optional convenience)
    data = fd.form_data or {}
    return data.get(path)


def parse_gps(value):
    """
    Handles:
      "-6.428527,37.262383"
      "-6.428527 37.262383"
      "-6.428527 37.262383 0 0" (ODK)
      {"latitude":..,"longitude":..} as dict (if you ever pass dict)
    """
    if value is None:
        return (None, None)

    if isinstance(value, dict):
        lat = value.get("latitude")
        lng = value.get("longitude")
        try:
            return (float(lat), float(lng))
        except Exception:
            return (None, None)

    s = str(value).strip()

    # split by comma OR whitespace
    parts = [p for p in re.split(r"[,\s]+", s) if p]
    if len(parts) < 2:
        return (None, None)

    try:
        return (float(parts[0]), float(parts[1]))
    except Exception:
        return (None, None)


def to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def to_iso_z(dt):
    if dt is None:
        return None

    # If it's already a string, keep it (or parse if you want)
    if isinstance(dt, str):
        return dt

    # If it's a datetime object
    if isinstance(dt, datetime):
        # ensure timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # format like 2025-07-27T20:42:46.682Z
        s = dt.astimezone(timezone.utc).isoformat(timespec="milliseconds")
        return s.replace("+00:00", "Z")

    return str(dt)


def map_value(config: FormPayloadConfig, entity_type: str, raw_value):
    """Map values"""
    if raw_value is None:
        return None
    key = str(raw_value).strip().lower()
    m = config.value_mappings.filter(entity_type=entity_type, source_value=key).first()
    return m.target_value if m else None


def apply_transform(value, transform: str, fd=None, config=None):
    if not transform:
        return value

    if transform == "iso_datetime":
        return to_iso_z(value)

    if transform == "to_float":
        return to_float(value)

    if transform == "gps_lat":
        lat, _ = parse_gps(value)
        return lat

    if transform == "gps_lng":
        _, lng = parse_gps(value)
        return lng

    # example: "map:species" (optional, if you use value mapping tables)
    if transform.startswith("map:") and config is not None:
        entity = transform.split(":", 1)[1].strip()
        return map_value(config, entity, value)  # you already have this function

    return value


def build_fields_payload(fd, config):
    """Build payload for all the fields"""
    payload = {}

    # Avoid N+1: ensure config.field_maps is prefetched where you call build_payload
    for fm in config.field_maps.all():
        # allow fallback:
        # "form_data.latitude || model.gps"
        paths = [p.strip() for p in (fm.form_data_path or "").split("||") if p.strip()]

        raw = None
        for p in paths:
            raw = get_value(fd, p)
            if raw not in (None, "", []):
                break

        if raw in (None, "", []) and fm.default_value is not None:
            raw = fm.default_value

        value = apply_transform(raw, fm.transform, fd=fd, config=config)

        if fm.required and value in (None, ""):
            raise ValueError(f"Missing required field: {fm.payload_field}")

        payload[fm.payload_field] = value

    return payload


def build_affected_animals(fd, config):
    """Build payload for affected animals"""
    data = fd.form_data or {}

    # 1) species
    species_raw = data.get("species")
    species_id = map_value(config, "species", species_raw)

    # 2) quantity (you used "quantity" in JSON)
    quantity = data.get("quantity") or data.get("idadi_dalili_wakubwa") or 0

    # 3) symptoms codes -> clinical_signs objects
    symptom_codes = data.get("symptoms", []) or []
    clinical_signs = []
    for code in symptom_codes:
        cs_id = map_value(config, "symptom", code)
        if cs_id:
            clinical_signs.append({"clinical_sign_id": cs_id})

    # If nothing meaningful, return [] not None (API-friendly)
    if not species_id and not clinical_signs and not quantity:
        return []

    return [
        {
            "species_id": species_id,  # can be None if missing mapping (your choice)
            "quantity": int(quantity) if quantity is not None else 0,
            "clinical_signs": clinical_signs,
        }
    ]


def build_payload(fd, config):
    """Build final payload by combining both"""
    payload = build_fields_payload(fd, config)
    payload["affected_animals"] = build_affected_animals(fd, config)
    return payload


def push_payload(cfg, payload):
    """Push data to endpoint"""
    if not cfg.endpoint:
        return False, {"error": "Missing endpoint in FormPayloadConfig"}

    method = (cfg.method or "POST").upper()

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if isinstance(cfg.headers, dict):
        headers.update(cfg.headers)

    try:
        resp = requests.request(
            method=method,
            url=cfg.endpoint,
            json=payload,
            headers=headers,
            timeout=25,
        )

        ok = 200 <= resp.status_code < 300
        info = {
            "ok": ok,
            "status_code": resp.status_code,
            "sent_at": timezone.now().isoformat(),
        }

        # keep a short response preview (avoid huge logs)
        try:
            info["response"] = resp.json()
        except Exception:
            info["response_text"] = (resp.text or "")[:500]

        if not ok:
            info["error"] = "Non-2xx response"

        return ok, info

    except Exception as e:
        return False, {
            "ok": False,
            "error": str(e),
            "sent_at": timezone.now().isoformat(),
        }
