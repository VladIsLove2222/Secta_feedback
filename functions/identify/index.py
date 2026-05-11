import asyncio
import json
import logging
import urllib.parse

from classifier import classify
from config import ALLOWED_ORIGINS, FORM_URLS
from facts import calculate
from phone import normalize, PhoneValidationError
from yclients import YClientsError, extract_tags, get_visits, search_client

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cors_headers(origin: str) -> dict:
    allowed = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    return {
        "Access-Control-Allow-Origin": allowed,
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Content-Type": "application/json",
    }


def _response(status_code: int, body: dict, origin: str = "") -> dict:
    return {
        "statusCode": status_code,
        "headers": _cors_headers(origin),
        "body": json.dumps(body, ensure_ascii=False),
    }


def _build_redirect_url(client_type: str, facts: dict) -> str:
    base = FORM_URLS.get(client_type, FORM_URLS["regular_anon"])
    params = {k: v for k, v in facts.items() if v is not None}
    qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"{base}?{qs}" if qs else base


# ---------------------------------------------------------------------------
# Core logic (async, reused from Render)
# ---------------------------------------------------------------------------

async def _identify_async(phone_raw: str) -> dict:
    try:
        phone = normalize(phone_raw)
    except PhoneValidationError as e:
        return {"_status_code": 400, "detail": str(e)}

    try:
        client_data = await search_client(phone)
    except YClientsError as e:
        logger.error(f"yclients search error: {e}")
        return {
            "status": "error",
            "redirect_url": FORM_URLS["regular_anon"],
        }

    if client_data is None:
        logger.info(f"client not found: {phone}")
        return {
            "status": "not_found",
            "redirect_url": FORM_URLS["regular_anon"],
        }

    try:
        visits_data = await get_visits(client_data["id"])
    except YClientsError as e:
        logger.error(f"yclients visits error: {e}")
        visits_data = []

    tags = extract_tags(visits_data)
    client_type = classify(client_data, tags)
    logger.info(
        f"client {client_data.get('name')}: "
        f"type={client_type} visits={client_data.get('visits_count')} tags={tags}"
    )

    facts = calculate(client_data, visits_data)
    redirect_url = _build_redirect_url(client_type, facts)

    return {
        "status": "ok",
        "client_type": client_type,
        "redirect_url": redirect_url,
    }


# ---------------------------------------------------------------------------
# Cloud Functions entry point
# ---------------------------------------------------------------------------

def handler(event, context):
    origin = (event.get("headers") or {}).get("origin", "")

    # CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": _cors_headers(origin), "body": ""}

    if event.get("httpMethod") != "POST":
        return _response(405, {"detail": "Method not allowed"}, origin)

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"detail": "Invalid JSON"}, origin)

    phone = body.get("phone", "").strip()
    if not phone:
        return _response(400, {"detail": "phone required"}, origin)

    result = asyncio.run(_identify_async(phone))

    status_code = result.pop("_status_code", 200)
    return _response(status_code, result, origin)
