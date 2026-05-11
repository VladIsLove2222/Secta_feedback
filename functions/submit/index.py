import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta

import ydb
import ydb.iam

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

YDB_ENDPOINT = os.environ["YDB_ENDPOINT"]
YDB_DATABASE = os.environ["YDB_DATABASE"]

ALLOWED_ORIGINS = [
    "https://sectabarbershop.ru",
    "http://localhost:3000",
]

HIDDEN_FIELDS = {"name", "master", "visits", "years", "money_saved", "hours", "hair_kg", "first_visit"}

MSK = timezone(timedelta(hours=3))

# ---------------------------------------------------------------------------
# YDB driver
# ---------------------------------------------------------------------------

_driver = None
_pool = None


def _get_pool() -> ydb.SessionPool:
    global _driver, _pool
    if _pool is not None:
        return _pool

    _driver = ydb.Driver(
        endpoint=YDB_ENDPOINT,
        database=YDB_DATABASE,
        credentials=ydb.iam.MetadataUrlCredentials(),
    )
    _driver.wait(fail_fast=True, timeout=5)
    _pool = ydb.SessionPool(_driver)
    return _pool


# ---------------------------------------------------------------------------
# YDB write
# ---------------------------------------------------------------------------

_UPSERT_QUERY = """
DECLARE $id AS Utf8;
DECLARE $form_type AS Utf8;
DECLARE $created_at AS Datetime;
DECLARE $nps_score AS Int32?;
DECLARE $master_name AS Utf8?;
DECLARE $master_work_rating AS Int32?;
DECLARE $atmosphere_rating AS Int32?;
DECLARE $params AS Json?;
DECLARE $answers AS Json?;

DECLARE $client_name AS Utf8?;
DECLARE $master_work AS Int32?;
DECLARE $master_human AS Int32?;
DECLARE $admin_rating AS Int32?;
DECLARE $agree AS Utf8?;
DECLARE $waited AS Utf8?;
DECLARE $warned AS Utf8?;
DECLARE $merch_want AS Utf8?;
DECLARE $merch_buy AS Utf8?;
DECLARE $notif_convenient AS Utf8?;
DECLARE $notif_disturb AS Utf8?;
DECLARE $notif_disturb_which AS Utf8?;
DECLARE $notif_useful AS Utf8?;
DECLARE $who_waiting AS Utf8?;
DECLARE $how_found AS Utf8?;
DECLARE $plan_return AS Utf8?;
DECLARE $service_done AS Utf8?;
DECLARE $master_bad_reasons AS Utf8?;
DECLARE $master_human_bad AS Utf8?;
DECLARE $money AS Utf8?;
DECLARE $new_services AS Utf8?;
DECLARE $m_cleanness AS Int32?;
DECLARE $m_music AS Int32?;
DECLARE $m_smell AS Int32?;
DECLARE $m_comfort AS Int32?;
DECLARE $m_coffee AS Int32?;
DECLARE $improve AS Utf8?;
DECLARE $nps_improve_7_8 AS Utf8?;
DECLARE $nps_improve_low AS Utf8?;
DECLARE $nps_improve_idiot AS Utf8?;
DECLARE $admin_bad_text AS Utf8?;
DECLARE $dont_change AS Utf8?;
DECLARE $contact_back AS Utf8?;

UPSERT INTO responses (
    id, form_type, created_at,
    nps_score, master_name, master_work_rating, atmosphere_rating,
    params, answers,
    client_name,
    master_work, master_human, admin_rating,
    agree, waited, warned,
    merch_want, merch_buy,
    notif_convenient, notif_disturb, notif_disturb_which, notif_useful,
    who_waiting, how_found, plan_return, service_done,
    master_bad_reasons, master_human_bad, money, new_services,
    m_cleanness, m_music, m_smell, m_comfort, m_coffee,
    improve, nps_improve_7_8, nps_improve_low, nps_improve_idiot,
    admin_bad_text, dont_change, contact_back
) VALUES (
    $id, $form_type, $created_at,
    $nps_score, $master_name, $master_work_rating, $atmosphere_rating,
    $params, $answers,
    $client_name,
    $master_work, $master_human, $admin_rating,
    $agree, $waited, $warned,
    $merch_want, $merch_buy,
    $notif_convenient, $notif_disturb, $notif_disturb_which, $notif_useful,
    $who_waiting, $how_found, $plan_return, $service_done,
    $master_bad_reasons, $master_human_bad, $money, $new_services,
    $m_cleanness, $m_music, $m_smell, $m_comfort, $m_coffee,
    $improve, $nps_improve_7_8, $nps_improve_low, $nps_improve_idiot,
    $admin_bad_text, $dont_change, $contact_back
);
"""


def _upsert(pool: ydb.SessionPool, row: dict):
    def callee(session):
        prepared = session.prepare(_UPSERT_QUERY)
        session.transaction().execute(prepared, row, commit_tx=True)

    pool.retry_operation_sync(callee)


# ---------------------------------------------------------------------------
# Payload parsing
# ---------------------------------------------------------------------------

def _to_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _to_str(val):
    """Строка или None. Пустая строка → None."""
    if val is None or val == "":
        return None
    return str(val)


def _list_to_str(val):
    """Массив → строка 'a, b, c'. Пустой массив → None."""
    if not val or not isinstance(val, list):
        return None
    parts = [str(x) for x in val if x is not None and str(x) != ""]
    return ", ".join(parts) if parts else None


def _parse_payload(body: dict) -> dict:
    form_type = body.get("type", "unknown")
    answers = body.get("answers") or {}
    params_from_form = body.get("params") or {}

    now_msk_naive = datetime.now(MSK).replace(tzinfo=None)
    epoch = datetime(1970, 1, 1)
    now_msk = int((now_msk_naive - epoch).total_seconds())

    params = params_from_form or {k: answers[k] for k in HIDDEN_FIELDS if k in answers}

    matrix = answers.get("matrix") or {}

    return {
        "$id": str(uuid.uuid4()),
        "$form_type": form_type,
        "$created_at": now_msk,

        # legacy/основные
        "$nps_score": _to_int(answers.get("nps")),
        "$master_name": _to_str(params.get("master") or answers.get("master")),
        "$master_work_rating": _to_int(answers.get("master_work")),
        "$atmosphere_rating": _to_int(answers.get("atmosphere")),
        "$params": json.dumps(params, ensure_ascii=False) if params else None,
        "$answers": json.dumps(answers, ensure_ascii=False),

        # client info
        "$client_name": _to_str(params.get("name")),

        # ratings
        "$master_work": _to_int(answers.get("master_work")),
        "$master_human": _to_int(answers.get("master_human")),
        "$admin_rating": _to_int(answers.get("admin_rating")),

        # single answers
        "$agree": _to_str(answers.get("agree")),
        "$waited": _to_str(answers.get("waited")),
        "$warned": _to_str(answers.get("warned")),
        "$merch_want": _to_str(answers.get("merch_want")),
        "$merch_buy": _to_str(answers.get("merch_buy")),
        "$notif_convenient": _to_str(answers.get("notif_convenient")),
        "$notif_disturb": _to_str(answers.get("notif_disturb")),
        "$notif_disturb_which": _to_str(answers.get("notif-disturb-which")),
        "$notif_useful": _to_str(answers.get("notif_useful")),
        "$who_waiting": _to_str(answers.get("who_waiting")),
        "$how_found": _to_str(answers.get("how_found")),
        "$plan_return": _to_str(answers.get("plan_return")),
        "$service_done": _to_str(answers.get("service_done")),

        # arrays
        "$master_bad_reasons": _list_to_str(answers.get("master_bad_reasons")),
        "$master_human_bad": _list_to_str(answers.get("master_human_bad")),
        "$money": _list_to_str(answers.get("money")),
        "$new_services": _list_to_str(answers.get("new_services")),

        # matrix
        "$m_cleanness": _to_int(matrix.get("cleanness")),
        "$m_music": _to_int(matrix.get("music")),
        "$m_smell": _to_int(matrix.get("smell")),
        "$m_comfort": _to_int(matrix.get("comfort")),
        "$m_coffee": _to_int(matrix.get("coffee")),

        # texts
        "$improve": _to_str(answers.get("improve")),
        "$nps_improve_7_8": _to_str(answers.get("nps-improve-7-8")),
        "$nps_improve_low": _to_str(answers.get("nps-improve-low")),
        "$nps_improve_idiot": _to_str(answers.get("nps-improve-idiot")),
        "$admin_bad_text": _to_str(answers.get("admin-bad-text")),
        "$dont_change": _to_str(answers.get("dont-change")),
        "$contact_back": _to_str(answers.get("contact_back")),
    }


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _cors_headers(origin: str) -> dict:
    allowed = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    return {
        "Access-Control-Allow-Origin": allowed,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Content-Type": "application/json",
    }


def _response(status_code: int, body: dict, origin: str = "") -> dict:
    return {
        "statusCode": status_code,
        "headers": _cors_headers(origin),
        "body": json.dumps(body, ensure_ascii=False),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def handler(event, context):
    origin = (event.get("headers") or {}).get("origin", "")

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": _cors_headers(origin), "body": ""}

    if event.get("httpMethod") != "POST":
        return _response(405, {"detail": "Method not allowed"}, origin)

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"detail": "Invalid JSON"}, origin)

    if not body.get("type") or not body.get("answers"):
        return _response(400, {"detail": "type and answers required"}, origin)

    try:
        row = _parse_payload(body)
        pool = _get_pool()
        _upsert(pool, row)
        logger.info(f"saved response id={row['$id']} type={row['$form_type']} nps={row['$nps_score']}")
    except Exception as e:
        logger.error(f"YDB write error: {e}")
        return _response(500, {"detail": "db write failed"}, origin)

    return _response(200, {"status": "ok", "id": row["$id"]}, origin)
