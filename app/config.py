import os

from dotenv import load_dotenv

# Загружаем переменные из .env (локально)
# На Render они задаются через веб-интерфейс
load_dotenv()


# --- yclients API ---

YCLIENTS_PARTNER_TOKEN = os.getenv("YCLIENTS_PARTNER_TOKEN")
YCLIENTS_USER_TOKEN = os.getenv("YCLIENTS_USER_TOKEN")
YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID")
YCLIENTS_BASE_URL = "https://api.yclients.com/api/v1"


# --- Классификация клиентов ---

# Сколько визитов нужно для статуса "бывалый"
REGULAR_MIN_VISITS = 16

# Сколько визитов нужно для статуса "сектант"
LOYAL_MIN_VISITS = 32

# Альтернативный критерий — процент скидки в профиле yclients
REGULAR_DISCOUNT = 5
LOYAL_DISCOUNT = 10

# Имя тега в yclients, который запускает жёсткую форму.
# Точное совпадение по полю `title` в client_tags.
# TODO: согласовать финальное имя с братом и вписать сюда.
HARDCORE_TAG = "hardcore"


# --- Формы Tally ---
# URL'ы заполнишь после создания всех форм

TALLY_FORMS = {
    "accompanying":  os.getenv("TALLY_FORM_ACCOMPANYING", ""),
    "newbie":        os.getenv("TALLY_FORM_NEWBIE", ""),
    "regular_anon":  os.getenv("TALLY_FORM_REGULAR_ANON", ""),
    "regular":       os.getenv("TALLY_FORM_REGULAR", ""),       # Бывалый
    "loyal":         os.getenv("TALLY_FORM_LOYAL", ""),         # Сектант
    "client":        os.getenv("TALLY_FORM_CLIENT", ""),        # Найден без скидки
    "hard":          os.getenv("TALLY_FORM_HARD", ""),          # Жёсткая (по тегу)
}


# --- Расчёт фактов ---

# Средний вес волос за одну стрижку (кг)
HAIR_PER_HAIRCUT_KG = 0.05

# Средний чек (руб) — для расчёта экономии через скидку
AVERAGE_CHECK = 1800

# Сопоставление staff_id из yclients → имя для опроса.
# Решает проблему "Имя Фамилия" vs "Фамилия Имя" и одинаковых имён (двух Саш).
# Для мастеров вне словаря используется fallback — их name из yclients как есть.
STAFF_NAMES = {
    4972359: "Денис",      # Денис Коршунов
    3495672: "Саша Б.",    # Александр Бодров
    1412958: "Саша Г.",    # Гогян Александр
    2379784: "Вова",       # Владимир Прохоров
    1415379: "Михаил",     # Кулябин Михаил
}


# --- CORS ---
# Домены, с которых разрешены запросы к API

ALLOWED_ORIGINS = [
    "https://sectabarbershop.ru",
    "http://localhost:3000",        # для локальной разработки
]
