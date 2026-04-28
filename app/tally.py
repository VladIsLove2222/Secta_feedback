from urllib.parse import urlencode
from app.config import TALLY_FORMS


def build_url(client_type: str, facts: dict | None = None) -> str:
    """
    Собирает URL формы Tally с hidden fields в query-параметрах.

    client_type: "loyal" | "regular" | "regular_anon" | "newbie" | "accompanying"
    facts: dict с данными клиента (для personalized форм) или None

    Возвращает:
        "https://tally.so/r/abc444?name=Иван&master=Костя&visits=24..."

    Для анонимных форм (regular_anon, newbie, accompanying) facts не нужны —
    возвращает голый URL без параметров.
    """
    base_url = TALLY_FORMS.get(client_type, "")

    if not base_url:
        raise ValueError(f"Неизвестный тип клиента: {client_type}")

    # Анонимные формы — без параметров
    if facts is None:
        return base_url

    # Убираем пустые значения — не засоряем URL
    params = {
        key: str(value)
        for key, value in facts.items()
        if value is not None and str(value) != ""
    }

    if not params:
        return base_url

    return f"{base_url}?{urlencode(params)}"


def get_anon_url(category: str) -> str:
    """
    Возвращает URL анонимной формы по категории с лендинга.

    category: "accompanying" | "newbie" | "regular_anon"

    Используется когда клиент не хочет идентифицироваться
    или нажал "Сопровождающий" / "Новичок" на лендинге.
    """
    return build_url(category)
