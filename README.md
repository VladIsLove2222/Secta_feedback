# Secta Barbershop — NPS Survey System

Бэкенд NPS-опросника для барбершопа [SECTA](https://sectabarbershop.ru). Клиент сканирует QR-код на стойке ресепшна, попадает на лендинг и видит форму, подобранную под его историю: новичок, лояльный сектант, сопровождающий или анонимный гость.

Система классифицирует клиента через [yclients API](https://api.yclients.com) (CRM барбершопа), строит форму с персонализированными фактами (мастер, визиты, сэкономленные деньги) и сохраняет ответы в Yandex Database для аналитики в DataLens.

---

## Архитектура

```
QR-код на стойке
      │
      ▼
Tilda-лендинг
      │  POST {phone}
      ▼
Yandex API Gateway
      │
      ├──────────────────────────────────┐
      ▼                                  ▼
functions/identify                 functions/submit
──────────────────                 ────────────────
1. Нормализация телефона           1. Парсинг ответов формы
2. Поиск клиента в yclients        2. Запись в YDB (30+ колонок)
3. Извлечение тегов (hardcore...)  3. Лог в Cloud Logging
4. Классификация (6 типов)              │
5. Сборка URL с фактами                 ▼
      │                            YDB (serverless)
      ▼                                 │
Tilda-форма (hard / loyal /             ▼
 client / newbie /              Yandex DataLens
 accomp / regular_anon)         (дашборд аналитики)
```

**6 типов клиентов:**

| Тип | Условие | Форма |
|-----|---------|-------|
| `hard` | тег `hardcore` в yclients | шутки, особый тон |
| `loyal` | скидка > 0% | Сектант, персональные факты |
| `client` | есть визиты, скидки нет | Постоянный клиент |
| `newbie` | 0 визитов | Новичок |
| `accomp` | сопровождающий | Отдельная форма |
| `regular_anon` | не найден в CRM | Анонимная форма |

---

## Стек

- **Python 3.12+** — Cloud Functions, бизнес-логика
- **Yandex Cloud Functions** — serverless-хостинг бэкенда
- **Yandex Database (YDB)** — хранилище ответов опросов
- **httpx** — async HTTP-клиент для yclients API
- **pytest + pytest-asyncio** — тесты
- **Vanilla JS + scroll-snap** — фронтенд форм
- **FastAPI** *(legacy, v1)* — предыдущий бэкенд на Render

---

## Структура репозитория

```
.
├── functions/
│   ├── identify/           # Cloud Function: идентификация клиента
│   │   ├── index.py        # handler — точка входа
│   │   ├── classifier.py   # логика классификации (6 типов)
│   │   ├── facts.py        # расчёт фактов (визиты, экономия, часы)
│   │   ├── yclients.py     # API-клиент yclients
│   │   ├── phone.py        # нормализация телефона
│   │   ├── names.py        # извлечение имени
│   │   ├── config.py       # конфиг (URL форм, env vars)
│   │   └── requirements.txt
│   └── submit/             # Cloud Function: сохранение ответов
│       ├── index.py        # handler + парсинг payload + запись в YDB
│       └── requirements.txt
│
├── tests/
│   ├── identify/           # Тесты для functions/identify
│   │   ├── conftest.py
│   │   ├── test_classifier.py
│   │   ├── test_facts.py
│   │   ├── test_handler.py
│   │   ├── test_names.py
│   │   ├── test_phone.py
│   │   └── test_yclients.py
│   └── submit/             # Тесты для functions/submit
│       ├── conftest.py
│       ├── test_helpers.py
│       ├── test_parse_payload.py
│       └── test_handler.py
│
├── forms/                  # README к HTML-формам и сами HTML-формы (залиты на Tilda)
├── app/                    # Legacy FastAPI-приложение (v1, не используется в проде)
│
├── .env.example            # Шаблон переменных окружения
├── pytest.ini
└── README.md
```

---

## Запуск тестов

```bash
# Установить зависимости
pip install -r requirements.txt   # или вручную: pytest pytest-asyncio httpx

# Запустить все тесты
pytest

# Только identify или только submit
pytest tests/identify
pytest tests/submit
```

Тесты не требуют реального yclients API и YDB — все внешние вызовы замоканы.

---

## История миграции

**v1 (legacy)** — FastAPI + Render:
- Монолитный FastAPI-сервис в `app/`
- Хостинг на [Render](https://render.com)
- Формы через [Tally](https://tally.so) с параметрами в URL
- Код в ветке `legacy/v1-render-fastapi`

**v2 (текущий)** — Yandex Cloud Functions + YDB:
- Две независимые функции: `identify` и `submit`
- Формы переехали на Tilda (встроены как кастомный HTML)
- Ответы сохраняются в YDB, аналитика в DataLens
- Убран тип `regular` (любая скидка → `loyal`)

---

## Автор

Влад Кулябин  
Telegram: [@Vlad1sLove14](https://t.me/Vlad1sLove14)  
Email: vladkul140902@yandex.ru
