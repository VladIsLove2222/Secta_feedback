from datetime import datetime

from config import HAIR_PER_HAIRCUT_KG, STAFF_NAMES
from names import extract_first_name


def calculate(client_data: dict, visits_data: list[dict]) -> dict:
    """
    Вычисляет интересные факты для подстановки в Tally.

    Возвращает:
    {
        "name": "Иван",
        "master": "Костя",
        "visits": 24,
        "years": "2 года 3 месяца",
        "money_saved": 18000,
        "hours": 36,
        "hair_kg": 1.2
    }
    """
    return {
        "name": _get_name(client_data),
        "master": _get_last_master(visits_data),
        "visits": client_data.get("visits_count", 0) or 0,
        "years": _format_years(client_data, visits_data),
        "money_saved": _calc_money_saved(visits_data),
        "hours": _calc_hours(visits_data),
        "hair_kg": _calc_hair(client_data),
    }


def _get_name(client_data: dict) -> str:
    """Имя клиента — обрезаем фамилию, скобки, запятые."""
    full_name = client_data.get("name", "") or ""
    first_name = extract_first_name(full_name)
    return first_name if first_name else "друг"


def _get_last_master(visits_data: list[dict]) -> str:
    """
    Имя мастера из последнего визита.

    Сначала пытаемся взять из STAFF_NAMES по staff_id (там лежат
    финальные имена для опроса — решает порядок имя/фамилия и двух Саш).
    Если staff_id нет в словаре — fallback на name из yclients как есть.
    """
    if not visits_data:
        return "твой мастер"

    last_visit = visits_data[0]  # визиты отсортированы от новых к старым
    staff = last_visit.get("staff")
    if not staff:
        return "твой мастер"

    staff_id = staff.get("id")
    if staff_id in STAFF_NAMES:
        return STAFF_NAMES[staff_id]

    return staff.get("name", "твой мастер") or "твой мастер"


def _format_years(client_data: dict, visits_data: list[dict] = None) -> str:
    """
    Форматирует время с нами в читаемый вид.

    Примеры: "2 года 3 месяца", "8 месяцев", "5 лет"

    Если first_visit_date нет в client_data — берём дату самого старого визита.
    """
    first_visit = client_data.get("first_visit_date")

    # Если нет в данных клиента — ищем в истории визитов
    if not first_visit and visits_data:
        oldest = _get_oldest_visit_date(visits_data)
        if oldest:
            first_visit = oldest

    if not first_visit:
        return "давно"

    try:
        if "T" in first_visit:
            first_date = datetime.fromisoformat(first_visit)
        else:
            first_date = datetime.strptime(first_visit[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return "давно"

    now = datetime.now()
    total_months = (now.year - first_date.year) * 12 + (now.month - first_date.month)

    if total_months < 0:
        return "недавно"

    years = total_months // 12
    months = total_months % 12

    if years == 0 and months == 0:
        return "меньше месяца"

    parts = []
    if years > 0:
        parts.append(_pluralize_years(years))
    if months > 0:
        parts.append(_pluralize_months(months))

    return " ".join(parts)


def _pluralize_years(n: int) -> str:
    """1 год, 2 года, 5 лет."""
    if 11 <= n % 100 <= 19:
        return f"{n} лет"
    last = n % 10
    if last == 1:
        return f"{n} год"
    if 2 <= last <= 4:
        return f"{n} года"
    return f"{n} лет"


def _pluralize_months(n: int) -> str:
    """1 месяц, 2 месяца, 5 месяцев."""
    if 11 <= n % 100 <= 19:
        return f"{n} месяцев"
    last = n % 10
    if last == 1:
        return f"{n} месяц"
    if 2 <= last <= 4:
        return f"{n} месяца"
    return f"{n} месяцев"


def _calc_money_saved(visits_data: list[dict]) -> int:
    """
    Фактическая экономия по истории визитов.

    Для каждой услуги: first_cost (без скидки) - cost_to_pay (по факту).
    Суммируем по всем услугам всех визитов.
    """
    total = 0
    for visit in visits_data:
        for service in visit.get("services", []) or []:
            first = service.get("first_cost", 0) or 0
            paid = service.get("cost_to_pay", 0) or 0
            total += max(0, first - paid)
    return int(total)


def _calc_hours(visits_data: list[dict]) -> float:
    """Суммарное время в кресле (часы)."""
    total_seconds = 0
    for visit in visits_data:
        length = visit.get("seance_length", 0) or 0
        total_seconds += length

    hours = total_seconds / 3600
    return round(hours, 1)


def _calc_hair(client_data: dict) -> float:
    """Условный вес волос (кг). Художественная оценка."""
    visits = client_data.get("visits_count", 0) or 0
    return round(visits * HAIR_PER_HAIRCUT_KG, 2)


def _get_oldest_visit_date(visits_data: list[dict]) -> str | None:
    """Находит дату самого старого визита в списке."""
    dates = []
    for visit in visits_data:
        date = visit.get("date") or visit.get("datetime")
        if date:
            dates.append(date[:10])  # берём только YYYY-MM-DD

    if not dates:
        return None

    return min(dates)
