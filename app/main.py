import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.classifier import classify
from app.config import ALLOWED_ORIGINS
from app.facts import calculate
from app.phone import normalize, PhoneValidationError
from app.tally import build_url, get_anon_url
from app.yclients import (
    YClientsError,
    extract_tags,
    get_visits,
    search_client,
)


# --- Логирование ---

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secta-feedback")


# --- FastAPI ---

app = FastAPI(
    title="SECTA Feedback API",
    description="Идентификация клиентов барбершопа SECTA для маршрутизации на формы опроса",
    version="1.0.0",
)

# CORS — разрешаем запросы с лендинга на Tilda
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# --- Схемы запросов/ответов ---

class IdentifyRequest(BaseModel):
    phone: str


class IdentifyResponse(BaseModel):
    status: str             # "ok" | "not_found" | "error"
    client_type: str | None = None
    redirect_url: str


# --- Эндпоинты ---

@app.post("/api/identify", response_model=IdentifyResponse)
async def identify(request: IdentifyRequest):
    """
    Главный эндпоинт.

    Принимает телефон → ищет клиента в yclients →
    классифицирует → возвращает URL формы Tally с данными.
    """

    # 1. Нормализация телефона
    try:
        phone = normalize(request.phone)
    except PhoneValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Поиск клиента в yclients
    try:
        client_data = await search_client(phone)
    except YClientsError as e:
        # API недоступен — отправляем на анонимную форму
        logger.error(f"yclients API ошибка: {e}")
        return IdentifyResponse(
            status="error",
            redirect_url=get_anon_url("regular_anon"),
        )

    # 3. Клиент не найден
    if client_data is None:
        logger.info(f"Клиент не найден: {phone}")
        return IdentifyResponse(
            status="not_found",
            redirect_url=get_anon_url("regular_anon"),
        )

    # 4. Получаем историю визитов
    try:
        visits_data = await get_visits(client_data["id"])
    except YClientsError as e:
        # Визиты не загрузились — отправляем с пустыми фактами
        logger.error(f"yclients visits ошибка: {e}")
        visits_data = []

    # 5. Извлекаем теги из визитов (без доп. запроса).
    # Если визитов нет — теги пустые, классифицируем без учёта тега
    # (договорённость, вариант А).
    tags = extract_tags(visits_data)

    # 6. Классификация с учётом тегов
    client_type = classify(client_data, tags)
    logger.info(
        f"Клиент {client_data.get('name')}: "
        f"тип={client_type}, визитов={client_data.get('visits_count')}, "
        f"теги={tags}"
    )

    # 7. Вычисление фактов
    facts = calculate(client_data, visits_data)

    # 8. Сборка URL
    redirect_url = build_url(client_type, facts)

    return IdentifyResponse(
        status="ok",
        client_type=client_type,
        redirect_url=redirect_url,
    )


@app.get("/api/forms")
async def get_forms():
    """
    Возвращает URL'ы анонимных форм.

    Лендинг использует это для кнопок "Сопровождающий" и "Новичок" —
    они не требуют идентификации, просто редирект.
    """
    return {
        "accompanying": get_anon_url("accompanying"),
        "newbie": get_anon_url("newbie"),
        "regular_anon": get_anon_url("regular_anon"),
    }


@app.get("/health")
async def health():
    """Для UptimeRobot — keep-alive."""
    return {"status": "ok"}
