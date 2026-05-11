import pytest
from names import extract_first_name


@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("Алексей Корешков", "Алексей"),
        ("Иван", "Иван"),
        ("X", "X"),
        ("Иван (бокс-фейд)", "Иван"),
        ("Михаил (любит покороче)", "Михаил"),
        ("Сергей (постоянник, скидка 10%)", "Сергей"),
        ("Дмитрий [VIP]", "Дмитрий"),
        ("Пётр, постоянник", "Пётр"),
        ("Андрей, тех. директор", "Андрей"),
        ("Анна-Мария", "Анна-Мария"),
        ("Жан-Поль Бельмондо", "Жан-Поль"),
        ("  Сергей  ", "Сергей"),
        ("  Алексей Корешков  ", "Алексей"),
        ("", ""),
        ("(заметка без имени)", ""),
        ("[только тег]", ""),
        (" ", ""),
    ],
)
def test_extract_first_name(input_name, expected):
    assert extract_first_name(input_name) == expected


def test_extract_first_name_handles_none_safely():
    assert extract_first_name(None) == ""
