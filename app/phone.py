import re


class PhoneValidationError(Exception):
    """Ошибка валидации телефона."""
    pass


def normalize(phone: str) -> str:
    """
    Приводит телефон к формату +7XXXXXXXXXX.

    Принимает:
        "+7 (999) 123-45-67"
        "8 999 123 45 67"
        "79991234567"
        "+79991234567"

    Возвращает:
        "+79991234567"

    Кидает PhoneValidationError если формат невалидный.
    """
    # Убираем всё кроме цифр
    digits = re.sub(r"\D", "", phone)

    # Если начинается с 8 и длина 11 — заменяем 8 на 7
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]

    # Если начинается с 7 и длина 11 — ок
    # Если длина 10 (без кода страны) — добавляем 7
    if len(digits) == 10:
        digits = "7" + digits

    # Финальная проверка
    if len(digits) != 11:
        raise PhoneValidationError(
            f"Неверная длина номера: {len(digits)} цифр (ожидается 11)"
        )

    if not digits.startswith("7"):
        raise PhoneValidationError(
            f"Номер должен начинаться с 7 или 8, получено: {digits[0]}"
        )

    return f"+{digits}"
