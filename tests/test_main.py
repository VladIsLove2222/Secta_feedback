import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# --- Фикстуры ---

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
        "services": [{"title": "Мужская стрижка", "cost": 1500}],
        "visit_attendance": 1,
    },
]

MOCK_FORMS = {
    "accompanying":  "https://tally.so/r/form1",
    "newbie":        "https://tally.so/r/form2",
    "regular_anon":  "https://tally.so/r/form3",
    "regular":       "https://tally.so/r/form4",
    "loyal":         "https://tally.so/r/form5",
}


@pytest.fixture(autouse=True)
def mock_forms():
    with patch("app.tally.TALLY_FORMS", MOCK_FORMS):
        yield


# --- POST /api/identify ---

class TestIdentify:

    def test_loyal_client(self):
        """Сектант найден → redirect на форму loyal с параметрами."""
        with patch("app.main.search_client", new_callable=AsyncMock) as mock_search, \
             patch("app.main.get_visits", new_callable=AsyncMock) as mock_visits:

            mock_search.return_value = SAMPLE_CLIENT
            mock_visits.return_value = SAMPLE_VISITS

            response = client.post(
                "/api/identify",
                json={"phone": "89991234567"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["client_type"] == "loyal"
        assert "tally.so/r/form5" in data["redirect_url"]
        assert "name=" in data["redirect_url"]
        assert "master=" in data["redirect_url"]

    def test_regular_client(self):
        """Бывалый (5 визитов, скидка 5%) → redirect на форму regular."""
        regular_client = {
            **SAMPLE_CLIENT,
            "visits_count": 5,
            "discount": 5,
        }

        with patch("app.main.search_client", new_callable=AsyncMock) as mock_search, \
             patch("app.main.get_visits", new_callable=AsyncMock) as mock_visits:

            mock_search.return_value = regular_client
            mock_visits.return_value = SAMPLE_VISITS

            response = client.post(
                "/api/identify",
                json={"phone": "+79991234567"},
            )

        data = response.json()
        assert data["status"] == "ok"
        assert data["client_type"] == "regular"
        assert "tally.so/r/form4" in data["redirect_url"]

    def test_client_not_found(self):
        """Клиент не найден → redirect на анонимную форму."""
        with patch("app.main.search_client", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = None

            response = client.post(
                "/api/identify",
                json={"phone": "+79991234567"},
            )

        data = response.json()
        assert data["status"] == "not_found"
        assert "tally.so/r/form3" in data["redirect_url"]

    def test_invalid_phone(self):
        """Невалидный телефон → 400."""
        response = client.post(
            "/api/identify",
            json={"phone": "abc"},
        )

        assert response.status_code == 400

    def test_yclients_api_down(self):
        """yclients не отвечает → fallback на анонимную форму."""
        from app.yclients import YClientsError

        with patch("app.main.search_client", new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = YClientsError("timeout")

            response = client.post(
                "/api/identify",
                json={"phone": "+79991234567"},
            )

        data = response.json()
        assert data["status"] == "error"
        assert "tally.so/r/form3" in data["redirect_url"]

    def test_visits_api_error_still_works(self):
        """Визиты не загрузились — клиент всё равно идентифицирован, факты пустые."""
        from app.yclients import YClientsError

        with patch("app.main.search_client", new_callable=AsyncMock) as mock_search, \
             patch("app.main.get_visits", new_callable=AsyncMock) as mock_visits:

            mock_search.return_value = SAMPLE_CLIENT
            mock_visits.side_effect = YClientsError("timeout")

            response = client.post(
                "/api/identify",
                json={"phone": "+79991234567"},
            )

        data = response.json()
        assert data["status"] == "ok"
        assert data["client_type"] == "loyal"
        assert "tally.so/r/form5" in data["redirect_url"]

    def test_phone_normalization(self):
        """Телефон в разных форматах — все работают."""
        with patch("app.main.search_client", new_callable=AsyncMock) as mock_search, \
             patch("app.main.get_visits", new_callable=AsyncMock) as mock_visits:

            mock_search.return_value = SAMPLE_CLIENT
            mock_visits.return_value = []

            # Формат с пробелами и скобками
            response = client.post(
                "/api/identify",
                json={"phone": "+7 (999) 123-45-67"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# --- GET /api/forms ---

class TestGetForms:

    def test_returns_anon_urls(self):
        response = client.get("/api/forms")

        assert response.status_code == 200
        data = response.json()
        assert "accompanying" in data
        assert "newbie" in data
        assert "regular_anon" in data
        assert data["accompanying"] == "https://tally.so/r/form1"


# --- GET /health ---

class TestHealth:

    def test_health_ok(self):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
