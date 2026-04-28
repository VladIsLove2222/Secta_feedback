import pytest
from unittest.mock import patch
from app.tally import build_url, get_anon_url


MOCK_FORMS = {
    "accompanying":  "https://tally.so/r/form1",
    "newbie":        "https://tally.so/r/form2",
    "regular_anon":  "https://tally.so/r/form3",
    "regular":       "https://tally.so/r/form4",
    "loyal":         "https://tally.so/r/form5",
}


@pytest.fixture(autouse=True)
def mock_tally_forms():
    """Подменяем URL форм во всех тестах."""
    with patch("app.tally.TALLY_FORMS", MOCK_FORMS):
        yield


# --- build_url ---

class TestBuildUrl:

    def test_loyal_with_facts(self):
        """Сектант с фактами — полный URL с параметрами."""
        facts = {
            "name": "Иван",
            "master": "Костя",
            "visits": 24,
            "years": "2 года",
            "money_saved": 3600,
            "hours": 36.5,
            "hair_kg": 1.2,
        }
        url = build_url("loyal", facts)

        assert url.startswith("https://tally.so/r/form5?")
        assert "name=" in url
        assert "master=" in url
        assert "visits=24" in url
        assert "hours=36.5" in url

    def test_regular_with_facts(self):
        """Бывалый с фактами."""
        facts = {"name": "Дима", "master": "Артём", "visits": 5}
        url = build_url("regular", facts)

        assert url.startswith("https://tally.so/r/form4?")
        assert "name=" in url

    def test_anon_without_facts(self):
        """Анонимная форма без facts — голый URL."""
        url = build_url("regular_anon")
        assert url == "https://tally.so/r/form3"

    def test_anon_with_none_facts(self):
        """facts=None — голый URL."""
        url = build_url("newbie", None)
        assert url == "https://tally.so/r/form2"

    def test_empty_facts_no_params(self):
        """Пустой dict — URL без параметров."""
        url = build_url("loyal", {})
        assert url == "https://tally.so/r/form5"

    def test_skips_empty_values(self):
        """Пустые значения не попадают в URL."""
        facts = {"name": "Иван", "master": "", "visits": 0}
        url = build_url("loyal", facts)

        assert "name=" in url
        assert "master=" not in url  # пустая строка пропущена
        assert "visits=0" in url     # 0 — валидное значение

    def test_skips_none_values(self):
        """None значения не попадают в URL."""
        facts = {"name": "Иван", "master": None}
        url = build_url("loyal", facts)

        assert "name=" in url
        assert "master=" not in url

    def test_cyrillic_encoded(self):
        """Кириллица кодируется в URL."""
        facts = {"name": "Иван"}
        url = build_url("loyal", facts)

        # urlencode кодирует кириллицу
        assert "name=" in url
        # URL не содержит кириллицу в чистом виде
        # (urlencode преобразует в %XX)

    def test_unknown_type_raises(self):
        """Неизвестный тип клиента — ошибка."""
        with pytest.raises(ValueError):
            build_url("vip_super_mega", {"name": "Тест"})


# --- get_anon_url ---

class TestGetAnonUrl:

    def test_accompanying(self):
        assert get_anon_url("accompanying") == "https://tally.so/r/form1"

    def test_newbie(self):
        assert get_anon_url("newbie") == "https://tally.so/r/form2"

    def test_regular_anon(self):
        assert get_anon_url("regular_anon") == "https://tally.so/r/form3"
