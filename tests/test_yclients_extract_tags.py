"""
ВАЖНО: Это НЕ полная замена test_yclients.py.
Это блок тестов, который нужно ДОБАВИТЬ в существующий test_yclients.py
(в самый конец файла, после класса TestGetVisits).

Существующие тесты search_client и get_visits не трогаем.
"""
from app.yclients import extract_tags


# --- extract_tags ---

class TestExtractTags:

    def test_no_visits(self):
        """Пустой список визитов — пустые теги."""
        assert extract_tags([]) == []

    def test_visits_without_client(self):
        """Визиты без объекта client — пустые теги."""
        visits = [{"id": 1, "date": "2026-04-10"}]
        assert extract_tags(visits) == []

    def test_visits_with_empty_tags(self):
        """В client есть, но client_tags пустой."""
        visits = [{"client": {"client_tags": []}}]
        assert extract_tags(visits) == []

    def test_single_tag(self):
        """Один тег."""
        visits = [{
            "client": {
                "client_tags": [
                    {"id": 1, "title": "hardcore"},
                ]
            }
        }]
        assert extract_tags(visits) == ["hardcore"]

    def test_multiple_tags(self):
        """Несколько тегов — порядок сохраняется."""
        visits = [{
            "client": {
                "client_tags": [
                    {"id": 1, "title": "Сарафан"},
                    {"id": 2, "title": "hardcore"},
                    {"id": 3, "title": "Через 4 недели"},
                ]
            }
        }]
        assert extract_tags(visits) == ["Сарафан", "hardcore", "Через 4 недели"]

    def test_tags_taken_from_first_visit_with_them(self):
        """Если в первом визите тегов нет — берём из следующего."""
        visits = [
            {"client": {}},  # без client_tags
            {"client": {"client_tags": [{"id": 1, "title": "hardcore"}]}},
        ]
        assert extract_tags(visits) == ["hardcore"]

    def test_tag_without_title(self):
        """Тег без title пропускается (защита от мусора в API)."""
        visits = [{
            "client": {
                "client_tags": [
                    {"id": 1, "title": "hardcore"},
                    {"id": 2},  # без title
                    {"id": 3, "title": ""},  # пустой title
                ]
            }
        }]
        assert extract_tags(visits) == ["hardcore"]
