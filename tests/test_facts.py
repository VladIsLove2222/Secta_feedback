import pytest
from datetime import datetime
from unittest.mock import patch
from app.facts import calculate, _format_years, _pluralize_years, _pluralize_months


# --- Фикстуры ---

SAMPLE_CLIENT = {
    "name": "Иван Петров",
    "phone": "+79991234567",
    "first_visit_date": "2024-01-15",
    "visits_count": 24,
    "discount": 10,
}

SAMPLE_VISITS = [
    {
        "date": "2026-04-10 14:00:00",
        "seance_length": 3600,
        "staff": {"id": 555, "name": "Костя"},
        "services": [{"first_cost": 2100, "cost_to_pay": 1890}],  # экономия 210
    },
    {
        "date": "2026-03-10 14:00:00",
        "seance_length": 2700,
        "staff": {"id": 555, "name": "Костя"},
        "services": [{"first_cost": 2100, "cost_to_pay": 1890}],  # экономия 210
    },
    {
        "date": "2026-02-10 14:00:00",
        "seance_length": 1800,
        "staff": {"id": 666, "name": "Дима"},
        "services": [{"first_cost": 2100, "cost_to_pay": 1890}],  # экономия 210
    },
]


# --- Полный расчёт ---

class TestCalculate:

    def test_full_calculation(self):
        """Полный расчёт с реальными данными."""
        result = calculate(SAMPLE_CLIENT, SAMPLE_VISITS)

        assert result["name"] == "Иван"
        assert result["master"] == "Костя"
        assert result["visits"] == 24
        assert result["money_saved"] == 630  # 3 визита × (2100 - 1890) = 630
        assert result["hours"] == 2.2  # (3600 + 2700 + 1800) / 3600
        assert result["hair_kg"] == 1.2  # 24 * 0.05

    def test_empty_data(self):
        """Пустые данные — не падает, возвращает дефолты."""
        result = calculate({}, [])

        assert result["name"] == "друг"
        assert result["master"] == "твой мастер"
        assert result["visits"] == 0
        assert result["money_saved"] == 0
        assert result["hours"] == 0
        assert result["hair_kg"] == 0

    def test_none_values(self):
        """None в полях — не падает."""
        client = {
            "name": None,
            "visits_count": None,
            "discount": None,
            "first_visit_date": None,
        }
        result = calculate(client, [])

        assert result["name"] == "друг"
        assert result["visits"] == 0
        assert result["money_saved"] == 0


# --- Имя ---

class TestGetName:

    def test_full_name_takes_first(self):
        result = calculate({"name": "Иван Петров"}, [])
        assert result["name"] == "Иван"

    def test_single_name(self):
        result = calculate({"name": "Иван"}, [])
        assert result["name"] == "Иван"

    def test_empty_name(self):
        result = calculate({"name": ""}, [])
        assert result["name"] == "друг"

    def test_name_with_spaces(self):
        result = calculate({"name": "  Иван  Петров  "}, [])
        assert result["name"] == "Иван"


# --- Мастер ---

class TestGetMaster:

    def test_master_from_last_visit(self):
        result = calculate({}, SAMPLE_VISITS)
        assert result["master"] == "Костя"

    def test_no_visits(self):
        result = calculate({}, [])
        assert result["master"] == "твой мастер"

    def test_no_staff_in_visit(self):
        visits = [{"date": "2026-04-10", "seance_length": 3600}]
        result = calculate({}, visits)
        assert result["master"] == "твой мастер"

    def test_staff_name_none(self):
        visits = [{"staff": {"name": None}, "seance_length": 3600}]
        result = calculate({}, visits)
        assert result["master"] == "твой мастер"


# --- Время с нами ---

class TestFormatYears:

    @patch("app.facts.datetime")
    def test_two_years_three_months(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 4, 20)
        mock_dt.fromisoformat = datetime.fromisoformat
        mock_dt.strptime = datetime.strptime
        result = _format_years({"first_visit_date": "2024-01-20"})
        assert result == "2 года 3 месяца"

    @patch("app.facts.datetime")
    def test_exactly_one_year(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 4, 20)
        mock_dt.fromisoformat = datetime.fromisoformat
        mock_dt.strptime = datetime.strptime
        result = _format_years({"first_visit_date": "2025-04-20"})
        assert result == "1 год"

    @patch("app.facts.datetime")
    def test_five_months(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 4, 20)
        mock_dt.fromisoformat = datetime.fromisoformat
        mock_dt.strptime = datetime.strptime
        result = _format_years({"first_visit_date": "2025-11-20"})
        assert result == "5 месяцев"

    def test_no_first_visit(self):
        assert _format_years({}) == "давно"

    def test_invalid_date(self):
        assert _format_years({"first_visit_date": "мусор"}) == "давно"


# --- Склонение ---

class TestPluralize:

    def test_years(self):
        assert _pluralize_years(1) == "1 год"
        assert _pluralize_years(2) == "2 года"
        assert _pluralize_years(3) == "3 года"
        assert _pluralize_years(4) == "4 года"
        assert _pluralize_years(5) == "5 лет"
        assert _pluralize_years(10) == "10 лет"
        assert _pluralize_years(11) == "11 лет"
        assert _pluralize_years(12) == "12 лет"
        assert _pluralize_years(21) == "21 год"
        assert _pluralize_years(22) == "22 года"

    def test_months(self):
        assert _pluralize_months(1) == "1 месяц"
        assert _pluralize_months(2) == "2 месяца"
        assert _pluralize_months(5) == "5 месяцев"
        assert _pluralize_months(11) == "11 месяцев"


# --- Экономия ---

class TestMoneySaved:

    def test_with_discount(self):
        visits = [{"services": [{"first_cost": 2000, "cost_to_pay": 1800}]}]
        result = calculate({"visits_count": 10, "discount": 10}, visits)
        assert result["money_saved"] == 200  # 2000 - 1800

    def test_zero_discount(self):
        result = calculate({"visits_count": 10, "discount": 0}, [])
        assert result["money_saved"] == 0

    def test_no_visits(self):
        result = calculate({"visits_count": 0, "discount": 10}, [])
        assert result["money_saved"] == 0


# --- Часы в кресле ---

class TestHours:

    def test_calculation(self):
        visits = [
            {"seance_length": 3600},  # 1 час
            {"seance_length": 1800},  # 0.5 часа
        ]
        result = calculate({}, visits)
        assert result["hours"] == 1.5

    def test_zero_length(self):
        visits = [{"seance_length": 0}]
        result = calculate({}, visits)
        assert result["hours"] == 0

    def test_missing_length(self):
        visits = [{"date": "2026-04-10"}]
        result = calculate({}, visits)
        assert result["hours"] == 0


# --- Волосы ---

class TestHair:

    def test_calculation(self):
        result = calculate({"visits_count": 20}, [])
        assert result["hair_kg"] == 1.0  # 20 * 0.05

    def test_zero_visits(self):
        result = calculate({"visits_count": 0}, [])
        assert result["hair_kg"] == 0
