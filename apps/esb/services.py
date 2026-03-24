import hashlib
from typing import Any, Dict, Tuple

import requests
from decouple import config
from django.core.cache import cache


DEFAULT_TOKEN_TIMEOUT = 30
DEFAULT_TOKEN_TTL = 3600
TOKEN_RESPONSE_SKEW = 60
MIN_CACHE_TIMEOUT = 30


class ESBTokenError(Exception):
    """Raised when the ESB bearer token cannot be fetched or parsed."""


def _get_token_settings() -> Tuple[str, str, str, int]:
    auth_url = config("ESB_AUTH_URL", default="").strip()
    username = config("ESB_AUTH_USERNAME", default="").strip()
    password = config("ESB_AUTH_PASSWORD", default="").strip()
    timeout = config("ESB_AUTH_TIMEOUT", default=DEFAULT_TOKEN_TIMEOUT, cast=int)

    missing = [
        name
        for name, value in (
            ("ESB_AUTH_URL", auth_url),
            ("ESB_AUTH_USERNAME", username),
            ("ESB_AUTH_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        raise ESBTokenError(f"Missing ESB auth configuration: {', '.join(missing)}")

    return auth_url, username, password, timeout


def _build_cache_key(auth_url: str, username: str) -> str:
    digest = hashlib.sha256(f"{auth_url}:{username}".encode("utf-8")).hexdigest()[:16]
    return f"external_api_token:{digest}"


def _parse_token_response(response: requests.Response) -> Dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        body_preview = (response.text or "")[:200]
        raise ESBTokenError(
            f"Token endpoint returned non-JSON response (status {response.status_code}): {body_preview}"
        ) from exc

    if not isinstance(data, dict):
        raise ESBTokenError(
            f"Token endpoint returned unexpected payload type: {type(data).__name__}"
        )

    return data


def _resolve_cache_timeout(expires_in: Any) -> int:
    try:
        ttl = int(expires_in or DEFAULT_TOKEN_TTL)
    except (TypeError, ValueError):
        ttl = DEFAULT_TOKEN_TTL

    return max(MIN_CACHE_TIMEOUT, ttl - TOKEN_RESPONSE_SKEW)


def get_bearer_token(force_refresh: bool = False) -> str:
    auth_url, username, password, timeout = _get_token_settings()
    cache_key = _build_cache_key(auth_url, username)

    if not force_refresh:
        cached_token = cache.get(cache_key)
        if cached_token:
            return cached_token

    payload = {
        "username": username,
        "password": password,
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            auth_url,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ESBTokenError(f"Failed to fetch ESB bearer token: {exc}") from exc

    data = _parse_token_response(response)

    token = (data.get("access_token") or data.get("token") or "").strip()
    if not token:
        raise ESBTokenError("Token missing in auth response")

    cache.set(cache_key, token, timeout=_resolve_cache_timeout(data.get("expires_in")))
    return token
