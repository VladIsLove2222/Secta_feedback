import pytest
from phone import normalize, PhoneValidationError


class TestNormalizeSuccess:

    def test_already_normalized(self):
        assert normalize("+79991234567") == "+79991234567"

    def test_with_8(self):
        assert normalize("89991234567") == "+79991234567"

    def test_with_spaces(self):
        assert normalize("8 999 123 45 67") == "+79991234567"

    def test_with_brackets_and_dashes(self):
        assert normalize("+7 (999) 123-45-67") == "+79991234567"

    def test_with_7_no_plus(self):
        assert normalize("79991234567") == "+79991234567"

    def test_without_country_code(self):
        assert normalize("9991234567") == "+79991234567"

    def test_mixed_separators(self):
        assert normalize("+7-999-123-45-67") == "+79991234567"

    def test_dots_as_separators(self):
        assert normalize("8.999.123.45.67") == "+79991234567"


class TestNormalizeFailure:

    def test_too_short(self):
        with pytest.raises(PhoneValidationError):
            normalize("123")

    def test_too_long(self):
        with pytest.raises(PhoneValidationError):
            normalize("+799912345678888")

    def test_empty_string(self):
        with pytest.raises(PhoneValidationError):
            normalize("")

    def test_only_letters(self):
        with pytest.raises(PhoneValidationError):
            normalize("abcdefghijk")

    def test_wrong_country_code(self):
        with pytest.raises(PhoneValidationError):
            normalize("+19991234567")
