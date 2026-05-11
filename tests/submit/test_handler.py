import json
from unittest.mock import patch, MagicMock

# submit_index зарегистрирован в sys.modules в conftest.py
import submit_index as _mod
from submit_index import handler


def make_event(method="POST", body=None, origin="https://sectabarbershop.ru"):
    return {
        "httpMethod": method,
        "headers": {"origin": origin},
        "body": json.dumps(body) if body is not None else None,
    }


VALID_BODY = {
    "type": "loyal",
    "answers": {"nps": "9", "master_work": "5"},
    "params": {"name": "Иван", "master": "Костя"},
}


# --- HTTP метод и preflight ---

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
        event["body"] = "не json{"
        resp = handler(event, {})
        assert resp["statusCode"] == 400
        assert "Invalid JSON" in resp["body"]

    def test_missing_type_returns_400(self):
        resp = handler(make_event("POST", body={"answers": {"nps": "9"}}), {})
        assert resp["statusCode"] == 400

    def test_missing_answers_returns_400(self):
        resp = handler(make_event("POST", body={"type": "loyal"}), {})
        assert resp["statusCode"] == 400

    def test_null_body_returns_400(self):
        event = make_event("POST")
        event["body"] = None
        resp = handler(event, {})
        assert resp["statusCode"] == 400


# --- Успешная запись ---

class TestSuccessfulWrite:

    def test_returns_200_with_id(self):
        with patch.object(_mod, "_get_pool") as mock_pool, \
             patch.object(_mod, "_upsert") as mock_upsert:
            mock_pool.return_value = MagicMock()
            mock_upsert.return_value = None

            resp = handler(make_event("POST", body=VALID_BODY), {})

        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["status"] == "ok"
        assert "id" in data

    def test_upsert_called_once(self):
        with patch.object(_mod, "_get_pool") as mock_pool, \
             patch.object(_mod, "_upsert") as mock_upsert:
            mock_pool.return_value = MagicMock()
            mock_upsert.return_value = None

            handler(make_event("POST", body=VALID_BODY), {})

        mock_upsert.assert_called_once()


# --- Ошибка YDB ---

class TestYdbError:

    def test_db_error_returns_500(self):
        with patch.object(_mod, "_get_pool") as mock_pool, \
             patch.object(_mod, "_upsert") as mock_upsert:
            mock_pool.return_value = MagicMock()
            mock_upsert.side_effect = Exception("YDB connection failed")

            resp = handler(make_event("POST", body=VALID_BODY), {})

        assert resp["statusCode"] == 500
        assert "db write failed" in resp["body"]


# --- CORS ---

class TestCors:

    def test_allowed_origin_echoed(self):
        with patch.object(_mod, "_get_pool"), patch.object(_mod, "_upsert"):
            resp = handler(make_event("POST", body=VALID_BODY,
                                      origin="https://sectabarbershop.ru"), {})

        assert resp["headers"]["Access-Control-Allow-Origin"] == "https://sectabarbershop.ru"

    def test_unknown_origin_gets_default(self):
        with patch.object(_mod, "_get_pool"), patch.object(_mod, "_upsert"):
            resp = handler(make_event("POST", body=VALID_BODY,
                                      origin="https://evil.com"), {})

        assert resp["headers"]["Access-Control-Allow-Origin"] == "https://sectabarbershop.ru"

    def test_options_has_cors_headers(self):
        event = {**make_event("OPTIONS"), "body": ""}
        resp = handler(event, {})
        assert "Access-Control-Allow-Origin" in resp["headers"]
        assert "Access-Control-Allow-Methods" in resp["headers"]
