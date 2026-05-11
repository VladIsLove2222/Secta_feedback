from config import HARDCORE_TAG


def classify(client_data: dict | None, tags: list[str] | None = None) -> str:
    """
    hard   — тег HARDCORE_TAG
    loyal  — любая скидка > 0
    client — найден, есть визиты, скидки нет
    newbie — найден, визитов 0
    """
    if client_data is None:
        return "not_found"

    if tags and HARDCORE_TAG in tags:
        return "hard"

    visits = client_data.get("visits_count", 0) or 0
    if visits == 0:
        return "newbie"

    discount = client_data.get("discount", 0) or 0
    if discount > 0:
        return "loyal"

    return "client"
