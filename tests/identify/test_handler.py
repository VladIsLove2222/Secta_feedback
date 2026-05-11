import json
from unittest.mock import AsyncMock, patch

# identify_index зарегистрирован в sys.modules в conftest.py
import identify_index as _mod
from identify_index import handler


def make_event(method="POST", body=None, origin="https://sectabarbershop.ru"):
    return {
        "httpMethod": method,
        "headers": {"origin": origin},
        "body": json.dumps(body) if body is not None else None,
    }


SAMPLE_CLIENT = {
    "id": 12345678,
    "name": "Иван Петров",
    "phone": "+79991234567",
    "first_visit_date": "2024-01-15",
    "visits_count": 24,
    "discount": 10,
}

SAMPLE_VISITS = [
    {
        "date": "2026-04-10 14:00:00",
        "seance_length": 3600,
        "staff": {"id": 555, "name": "Костя"},
        "services": [{"first_cost": 2100, "cost_to_pay": 1890}],
        "visit_attendance": 1,
    }
]


# --- Preflight и метод ---

class TestHttpMethod:

    def test_options_returns_204(self):
        event = {**make_event("OPTIONS"), "body": ""}
        resp = handler(event, {})
        assert resp["statusCode"] == 204

    def test_get_returns_405(self):
        resp = handler(make_event("GET"), {})
        assert resp["statusCode"] == 405

    def test_put_returns_405(self):
        resp = handler(make_event("PUT"), {})
        assert resp["statusCode"] == 405


# --- Валидация body ---

class TestBodyValidation:

    def test_invalid_json_returns_400(self):
        event = make_event("POST")
        event["body"] = "не JSON{"
        resp = handler(event, {})
        assert resp["statusCode"] == 400
        assert "Invalid JSON" in resp["body"]

    def test_missing_phone_returns_400(self):
        resp = handler(make_event("POST", body={}), {})
        assert resp["statusCode"] == 400
        assert "phone" in resp["body"]

    def test_empty_phone_returns_400(self):
        resp = handler(make_event("POST", body={"phone": "  "}), {})
        assert resp["statusCode"] == 400

    def test_null_body_treated_as_empty(self):
        event = make_event("POST")
        event["body"] = None
        resp = handler(event, {})
        assert resp["statusCode"] == 400


# --- Бизнес-логика ---

class TestIdentifyLogic:

    def test_loyal_client(self):
        with patch.object(_mod, "search_client", new_callable=AsyncMock) as mock_search, \
             patch.object(_mod, "get_visits", new_callable=AsyncMock) as mock_visits:
            mock_search.return_value = SAMPLE_CLIENT
            mock_visits.return_value = SAMPLE_VISITS

            resp = handler(make_event("POST", body={"phone": "89991234567"}), {})

        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["status"] == "ok"
        assert data["client_type"] == "loyal"
        assert "redirect_url" in data

    def test_client_not_found(self):
        with patch.object(_mod, "search_client", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = None

            resp = handler(make_event("POST", body={"phone": "+79991234567"}), {})

        data = json.loads(resp["body"])
        assert data["status"] == "not_found"
        assert "regular_anon" in data["redirect_url"]

    def test_yclients_error_returns_error_status(self):
        from yclients import YClientsError
        with patch.object(_mod, "search_client", new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = YClientsError("timeout")

            resp = handler(make_event("POST", body={"phone": "+79991234567"}), {})

        data = json.loads(resp["body"])
        assert data["status"] == "error"
        assert "regular_anon" in data["redirect_url"]

    def test_visits_error_still_identifies_client(self):
        from yclients import YClientsError
        with patch.object(_mod, "search_client", new_callable=AsyncMock) as mock_search, \
             patch.object(_mod, "get_visits", new_callable=AsyncMock) as mock_visits:
            mock_search.return_value = SAMPLE_CLIENT
            mock_visits.side_effect = YClientsError("timeout")

            resp = handler(make_event("POST", body={"phone": "+79991234567"}), {})

        data = json.loads(resp["body"])
        assert data["status"] == "ok"
        assert data["client_type"] == "loyal"

    def test_invalid_phone_format_returns_400(self):
        resp = handler(make_event("POST", body={"phone": "abc"}), {})
        assert resp["statusCode"] == 400

    def test_phone_normalization(self):
        with patch.object(_mod, "search_client", new_callable=AsyncMock) as mock_search, \
             patch.object(_mod, "get_visits", new_callable=AsyncMock) as mock_visits:
            mock_search.return_value = SAMPLE_CLIENT
            mock_visits.return_value = []

            resp = handler(make_event("POST", body={"phone": "+7 (999) 123-45-67"}), {})

        assert resp["statusCode"] == 200


# --- CORS ---

class TestCors:

    def test_allowed_origin_echoed(self):
        with patch.object(_mod, "search_client", new_callable=AsyncMock) as m:
            m.return_value = None
            resp = handler(make_event("POST", body={"phone": "+79991234567"},
                                      origin="https://sectabarbershop.ru"), {})

        assert resp["headers"]["Access-Control-Allow-Origin"] == "https://sectabarbershop.ru"

    def test_unknown_origin_gets_default(self):
        with patch.object(_mod, "search_client", new_callable=AsyncMock) as m:
            m.return_value = None
            resp = handler(make_event("POST", body={"phone": "+79991234567"},
                                      origin="https://evil.com"), {})

        assert resp["headers"]["Access-Control-Allow-Origin"] == "https://sectabarbershop.ru"

    def test_options_has_cors_headers(self):
        event = {**make_event("OPTIONS", origin="https://sectabarbershop.ru"), "body": ""}
        resp = handler(event, {})
        assert "Access-Control-Allow-Origin" in resp["headers"]
        assert "Access-Control-Allow-Methods" in resp["headers"]
