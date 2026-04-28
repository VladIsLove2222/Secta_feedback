import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.yclients import search_client, get_visits, YClientsError


# --- Фикстуры: типичные ответы API ---

def make_response(status_code: int, json_data: dict):
    """Создаёт мок HTTP-ответа."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.text = str(json_data)
    return mock


CLIENT_FOUND_RESPONSE = {
    "data": [
        {
            "id": 12345678,
            "name": "Иван",
            "phone": "+79991234567",
            "first_visit_date": "2022-03-15",
            "visits_count": 24,
            "discount": 10,
        }
    ]
}

CLIENT_NOT_FOUND_RESPONSE = {
    "data": []
}

VISITS_RESPONSE = {
    "data": [
        {
            "date": "2026-04-10 14:00:00",
            "seance_length": 3600,
            "staff": {"id": 555, "name": "Костя"},
            "services": [{"title": "Мужская стрижка", "cost": 1500}],
            "visit_attendance": 1,
        },
        {
            "date": "2026-03-10 14:00:00",
            "seance_length": 2700,
            "staff": {"id": 555, "name": "Костя"},
            "services": [{"title": "Моделирование бороды", "cost": 800}],
            "visit_attendance": 1,
        },
        {
            "date": "2026-02-10 14:00:00",
            "seance_length": 3600,
            "staff": {"id": 666, "name": "Дима"},
            "services": [{"title": "Мужская стрижка", "cost": 1500}],
            "visit_attendance": 0,  # не пришёл — должен отфильтроваться
        },
    ]
}


# --- Тесты search_client ---

class TestSearchClient:

    @pytest.mark.asyncio
    async def test_client_found(self):
        """Клиент найден — возвращает dict с данными."""
        mock_response = make_response(200, CLIENT_FOUND_RESPONSE)

        with patch("app.yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await search_client("+79991234567")

        assert result is not None
        assert result["name"] == "Иван"
        assert result["visits_count"] == 24
        assert result["discount"] == 10

    @pytest.mark.asyncio
    async def test_client_not_found(self):
        """Клиент не найден — возвращает None."""
        mock_response = make_response(200, CLIENT_NOT_FOUND_RESPONSE)

        with patch("app.yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await search_client("+79991234567")

        assert result is None

    @pytest.mark.asyncio
    async def test_api_error_status(self):
        """API вернул ошибку (не 200) — кидает YClientsError."""
        mock_response = make_response(500, {"error": "Internal Server Error"})

        with patch("app.yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            with pytest.raises(YClientsError):
                await search_client("+79991234567")


# --- Тесты get_visits ---

class TestGetVisits:

    @pytest.mark.asyncio
    async def test_visits_returned(self):
        """Визиты получены, неявившиеся отфильтрованы."""
        mock_response = make_response(200, VISITS_RESPONSE)

        with patch("app.yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_visits(12345678)

        # Было 3 визита, но visit_attendance=0 отфильтрован
        assert len(result) == 2
        assert result[0]["staff"]["name"] == "Костя"

    @pytest.mark.asyncio
    async def test_empty_visits(self):
        """У клиента нет визитов — пустой список."""
        mock_response = make_response(200, {"data": []})

        with patch("app.yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_visits(12345678)

        assert result == []

    @pytest.mark.asyncio
    async def test_api_error_status(self):
        """API вернул ошибку — кидает YClientsError."""
        mock_response = make_response(403, {"error": "Forbidden"})

        with patch("app.yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            with pytest.raises(YClientsError):
                await get_visits(12345678)
