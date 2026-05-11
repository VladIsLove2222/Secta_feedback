import os

# --- yclients ---
YCLIENTS_PARTNER_TOKEN = os.environ["YCLIENTS_PARTNER_TOKEN"]
YCLIENTS_USER_TOKEN = os.environ["YCLIENTS_USER_TOKEN"]
YCLIENTS_COMPANY_ID = os.environ["YCLIENTS_COMPANY_ID"]
YCLIENTS_BASE_URL = "https://api.yclients.com/api/v1"

# --- Классификация ---
HARDCORE_TAG = "hardcore"

# --- Формы Tilda ---
FORM_URLS = {
    "hard":         "https://sectabarbershop.ru/hard",
    "loyal":        "https://sectabarbershop.ru/loyal",
    "client":       "https://sectabarbershop.ru/client",
    "regular_anon": "https://sectabarbershop.ru/regular_anon",
    "newbie":       "https://sectabarbershop.ru/newbie",
    "accomp":       "https://sectabarbershop.ru/accomp",
}

# --- Факты ---
HAIR_PER_HAIRCUT_KG = 0.05

STAFF_NAMES = {
    4972359: "Денис",
    3495672: "Саша Б.",
    1412958: "Саша Г.",
    2379784: "Вова",
    1415379: "Михаил",
}

# --- CORS ---
ALLOWED_ORIGINS = [
    "https://sectabarbershop.ru",
    "http://localhost:3000",
]
