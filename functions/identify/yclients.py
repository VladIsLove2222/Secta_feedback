import httpx

from config import (
    YCLIENTS_BASE_URL,
    YCLIENTS_COMPANY_ID,
    YCLIENTS_PARTNER_TOKEN,
    YCLIENTS_USER_TOKEN,
)


class YClientsError(Exception):
    """Ошибка при работе с yclients API."""
    pass


def _get_headers() -> dict:
    """Заголовки для всех запросов к yclients."""
    return {
        "Authorization": f"Bearer {YCLIENTS_PARTNER_TOKEN}, User {YCLIENTS_USER_TOKEN}",
        "Accept": "application/vnd.api.v2+json",
        "Content-Type": "application/json",
    }


async def search_client(phone: str) -> dict | None:
    """
    Ищет клиента по телефону в базе yclients.

    Возвращает dict с данными клиента или None если не найден.

    Пример ответа:
    {
        "id": 12345678,
        "name": "Иван",
        "phone": "+79991234567",
        "first_visit_date": "2022-03-15",
        "visits_count": 24,
        "discount": 10
    }
    """
    url = f"{YCLIENTS_BASE_URL}/company/{YCLIENTS_COMPANY_ID}/clients/search"

    body = {
        "fields": [
            "id", "name", "phone",
            "first_visit_date", "visits_count",
            "discount",
        ],
        "filters": [
            {
                "type": "quick_search",
                "state": {"value": phone},
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=_get_headers(),
                json=body,
            )

        if response.status_code != 200:
            raise YClientsError(
                f"yclients вернул {response.status_code}: {response.text[:200]}"
            )

        data = response.json()

        # API возвращает {"data": [...], "meta": {...}}
        # Если список пустой — клиент не найден
        clients = data.get("data", [])
        if not clients:
            return None

        return clients[0]

    except httpx.TimeoutException:
        raise YClientsError("yclients API не ответил за 10 секунд")
    except httpx.RequestError as e:
        raise YClientsError(f"Ошибка соединения с yclients: {e}")


async def get_visits(client_id: int) -> list[dict]:
    """
    Получает историю визитов клиента.

    Возвращает список визитов от новых к старым.

    Каждый визит содержит:
    {
        "date": "2026-04-10 14:00:00",
        "seance_length": 3600,
        "staff": {"id": 555, "name": "Костя"},
        "services": [{"title": "Мужская стрижка", "cost": 1500}],
        "visit_attendance": 1
    }
    """
    url = f"{YCLIENTS_BASE_URL}/records/{YCLIENTS_COMPANY_ID}"

    params = {
        "client_id": client_id,
        "count": 200,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers=_get_headers(),
                params=params,
            )

        if response.status_code != 200:
            raise YClientsError(
                f"yclients вернул {response.status_code}: {response.text[:200]}"
            )

        data = response.json()

        # Фильтруем: только реально состоявшиеся визиты
        visits = data.get("data", [])
        return [v for v in visits if v.get("visit_attendance") == 1]

    except httpx.TimeoutException:
        raise YClientsError("yclients API не ответил за 10 секунд")
    except httpx.RequestError as e:
        raise YClientsError(f"Ошибка соединения с yclients: {e}")


def extract_tags(visits: list[dict]) -> list[str]:
    """
    Достаёт теги клиента из ответа /records.

    yclients не отдаёт теги через /clients/search — они приходят
    только в каждом визите внутри объекта record.client.client_tags.
    Берём из первого попавшегося визита (теги на уровне клиента,
    одинаковые во всех его визитах).

    Возвращает список title тегов: ["Сарафан", "Через 4 недели", ...]
    Если визитов нет — пустой список (см. договорённость, вариант А).
    """
    if not visits:
        return []

    for visit in visits:
        client = visit.get("client") or {}
        tags = client.get("client_tags")
        if tags:
            return [t.get("title", "") for t in tags if t.get("title")]

    return []
