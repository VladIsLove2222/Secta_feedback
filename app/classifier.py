from app.config import (
    HARDCORE_TAG,
    LOYAL_DISCOUNT,
    REGULAR_DISCOUNT,
)


def classify(client_data: dict | None, tags: list[str] | None = None) -> str:
    """
    Определяет тип клиента и форму, на которую его отправить.

    Порядок проверок (важен — первое совпадение побеждает):
        1. Клиент не найден в yclients          → "not_found"
        2. Есть тег HARDCORE_TAG                → "hard"
        3. visits_count == 0                    → "newbie"
        4. discount >= LOYAL_DISCOUNT (10%)     → "loyal"
        5. discount >= REGULAR_DISCOUNT (5%)    → "regular"
        6. Найден, но скидки нет                → "client"

    tags — список title тегов клиента (см. yclients.extract_tags).
    Если None или пустой — считаем, что тегов нет.
    """
    if client_data is None:
        return "not_found"

    # 1. Тег hardcore — высший приоритет.
    # Ставится друзьям лично, важнее статуса лояльности.
    if tags and HARDCORE_TAG in tags:
        return "hard"

    discount = client_data.get("discount", 0) or 0
    visits = client_data.get("visits_count", 0) or 0

    # 2. Найден в базе, но визитов ещё нет — отправляем как новичка.
    if visits == 0:
        return "newbie"

    # 3. Сектант
    if discount >= LOYAL_DISCOUNT:
        return "loyal"

    # 4. Бывалый
    if discount >= REGULAR_DISCOUNT:
        return "regular"

    # 5. Найден в базе, есть визиты, но скидки нет (новый тип).
    return "client"
