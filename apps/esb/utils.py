import re
import ast
import json
import requests
import logging
from datetime import datetime, date, timezone as dt_timezone
from django.utils.dateparse import parse_datetime, parse_date
from apps.esb.services import get_auth_headers

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
      - model
      - form_data
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
        lat = value.get("latitude", value.get("lat"))
        lng = value.get("longitude", value.get("lng"))

        try:
            return (float(lat), float(lng))
        except Exception:
            return (None, None)

    s = str(value).strip()

    # DB varchar can store dict-like string payloads
    if s.startswith("{") and s.endswith("}"):
        parsed = None
        try:
            parsed = json.loads(s)
        except Exception:
            try:
                parsed = ast.literal_eval(s)
            except Exception:
                parsed = None

        if isinstance(parsed, dict):
            return parse_gps(parsed)

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

    if isinstance(dt, datetime):
        # Ensure timezone-aware and serialize in UTC with trailing Z
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_timezone.utc)

        s = dt.astimezone(dt_timezone.utc).isoformat(timespec="milliseconds")
        return s.replace("+00:00", "Z")

    # Support date objects by normalizing to midnight UTC
    if isinstance(dt, date):
        d = datetime(dt.year, dt.month, dt.day, tzinfo=dt_timezone.utc)
        s = d.isoformat(timespec="milliseconds")
        return s.replace("+00:00", "Z")

    # Normalize parseable date/datetime strings to ISO UTC + Z
    if isinstance(dt, str):
        s = dt.strip()
        if not s:
            return None

        parsed_dt = parse_datetime(s)
        if parsed_dt is not None:
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=dt_timezone.utc)
            out = parsed_dt.astimezone(dt_timezone.utc).isoformat(timespec="milliseconds")
            return out.replace("+00:00", "Z")

        parsed_date = parse_date(s)
        if parsed_date is not None:
            d = datetime(
                parsed_date.year,
                parsed_date.month,
                parsed_date.day,
                tzinfo=dt_timezone.utc,
            )
            out = d.isoformat(timespec="milliseconds")
            return out.replace("+00:00", "Z")

        return dt

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
    numb_of_young_show_sympt = data.get("numb_of_young_show_sympt") or 0
    numb_of_adult_show_sympt = data.get("numb_of_adult_show_sympt") or 0
    quantity =  numb_of_adult_show_sympt + numb_of_young_show_sympt

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
    payload["original_payload"] = fd.form_data
    payload["affected_animals"] = build_affected_animals(fd, config)
    return payload


def push_payload(cfg, payload, formdata=None):
    """Push data to endpoint"""
    if not cfg.endpoint:
        return False, {"error": "Missing endpoint in FormPayloadConfig"}

    # method
    method = (cfg.method or "POST").upper()

    # header
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # check if header passed from db
    if isinstance(cfg.headers, dict):
        headers.update(cfg.headers)

    # pass authorization header
    if not headers.get("Authorization"):
        headers.update(get_auth_headers())

    try:
        resp = requests.request(
            method=method,
            url=cfg.endpoint,
            json=payload,
            headers=headers,
            timeout=25,
        )
        try:
            response_body = resp.json()
        except Exception:
            response_body = {"raw": (resp.text or "")[:2000]}

        logging.info("== API Response ==")
        logging.info(resp.status_code)
        logging.info(response_body)
        
        ok = 200 <= resp.status_code < 300
        info = {
            "ok": ok,
            "status_code": resp.status_code,
            "sent_at": datetime.now(),
            "response": response_body,
        }

        if not ok:
            info["error"] = "Failed to post data"
        elif formdata is not None:
            response_id = None
            if isinstance(response_body, dict):
                response_id = (
                    response_body.get("response_id")
                    or response_body.get("id")
                    or response_body.get("uuid")
                )
                if response_id is None and isinstance(response_body.get("data"), dict):
                    response_id = (
                        response_body["data"].get("response_id")
                        or response_body["data"].get("id")
                        or response_body["data"].get("uuid")
                    )

            update_fields = {
                "response_json": response_body if isinstance(response_body, dict) else {"response": response_body},
                "push_status": True,
            }
            if response_id not in (None, ""):
                update_fields["response_id"] = str(response_id)
            formdata.__class__.objects.filter(pk=formdata.pk).update(**update_fields)

        return ok, info

    except Exception as e:
        return False, {
            "ok": False,
            "error": str(e),
            "sent_at": datetime.now(),
        }
