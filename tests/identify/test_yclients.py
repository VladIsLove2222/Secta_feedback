import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from yclients import search_client, get_visits, extract_tags, YClientsError


def make_response(status_code: int, json_data: dict):
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

CLIENT_NOT_FOUND_RESPONSE = {"data": []}

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
            "visit_attendance": 0,  # не пришёл — фильтруется
        },
    ]
}


# --- search_client ---

class TestSearchClient:

    @pytest.mark.asyncio
    async def test_client_found(self):
        mock_response = make_response(200, CLIENT_FOUND_RESPONSE)

        with patch("yclients.httpx.AsyncClient") as MockClient:
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
        mock_response = make_response(200, CLIENT_NOT_FOUND_RESPONSE)

        with patch("yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await search_client("+79991234567")

        assert result is None

    @pytest.mark.asyncio
    async def test_api_error_status(self):
        mock_response = make_response(500, {"error": "Internal Server Error"})

        with patch("yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            with pytest.raises(YClientsError):
                await search_client("+79991234567")


# --- get_visits ---

class TestGetVisits:

    @pytest.mark.asyncio
    async def test_visits_returned_and_filtered(self):
        mock_response = make_response(200, VISITS_RESPONSE)

        with patch("yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_visits(12345678)

        assert len(result) == 2
        assert result[0]["staff"]["name"] == "Костя"

    @pytest.mark.asyncio
    async def test_empty_visits(self):
        mock_response = make_response(200, {"data": []})

        with patch("yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_visits(12345678)

        assert result == []

    @pytest.mark.asyncio
    async def test_api_error_status(self):
        mock_response = make_response(403, {"error": "Forbidden"})

        with patch("yclients.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            with pytest.raises(YClientsError):
                await get_visits(12345678)


# --- extract_tags ---

class TestExtractTags:

    def test_no_visits(self):
        assert extract_tags([]) == []

    def test_visits_without_client(self):
        visits = [{"id": 1, "date": "2026-04-10"}]
        assert extract_tags(visits) == []

    def test_visits_with_empty_tags(self):
        visits = [{"client": {"client_tags": []}}]
        assert extract_tags(visits) == []

    def test_single_tag(self):
        visits = [{"client": {"client_tags": [{"id": 1, "title": "hardcore"}]}}]
        assert extract_tags(visits) == ["hardcore"]

    def test_multiple_tags(self):
        visits = [{
            "client": {
                "client_tags": [
                    {"id": 1, "title": "Сарафан"},
                    {"id": 2, "title": "hardcore"},
                    {"id": 3, "title": "Через 4 недели"},
                ]
            }
        }]
        assert extract_tags(visits) == ["Сарафан", "hardcore", "Через 4 недели"]

    def test_tags_from_first_visit_with_them(self):
        visits = [
            {"client": {}},
            {"client": {"client_tags": [{"id": 1, "title": "hardcore"}]}},
        ]
        assert extract_tags(visits) == ["hardcore"]

    def test_tag_without_title_skipped(self):
        visits = [{
            "client": {
                "client_tags": [
                    {"id": 1, "title": "hardcore"},
                    {"id": 2},
                    {"id": 3, "title": ""},
                ]
            }
        }]
        assert extract_tags(visits) == ["hardcore"]
