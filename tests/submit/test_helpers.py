from submit_index import _to_int, _to_str, _list_to_str


class TestToInt:

    def test_int_value(self):
        assert _to_int(5) == 5

    def test_string_number(self):
        assert _to_int("10") == 10

    def test_none_returns_none(self):
        assert _to_int(None) is None

    def test_empty_string_returns_none(self):
        assert _to_int("") is None

    def test_non_numeric_string_returns_none(self):
        assert _to_int("abc") is None

    def test_float_string_returns_none(self):
        # "3.5" не конвертируется в int
        assert _to_int("3.5") is None

    def test_zero(self):
        assert _to_int(0) == 0

    def test_negative(self):
        assert _to_int(-1) == -1


class TestToStr:

    def test_regular_string(self):
        assert _to_str("hello") == "hello"

    def test_none_returns_none(self):
        assert _to_str(None) is None

    def test_empty_string_returns_none(self):
        assert _to_str("") is None

    def test_int_converts_to_str(self):
        assert _to_str(42) == "42"

    def test_whitespace_preserved(self):
        assert _to_str("  ") == "  "


class TestListToStr:

    def test_simple_list(self):
        assert _list_to_str(["a", "b", "c"]) == "a, b, c"

    def test_none_returns_none(self):
        assert _list_to_str(None) is None

    def test_empty_list_returns_none(self):
        assert _list_to_str([]) is None

    def test_not_a_list_returns_none(self):
        assert _list_to_str("строка") is None

    def test_none_elements_skipped(self):
        assert _list_to_str(["a", None, "b"]) == "a, b"

    def test_empty_string_elements_skipped(self):
        assert _list_to_str(["a", "", "b"]) == "a, b"

    def test_all_empty_elements_returns_none(self):
        assert _list_to_str(["", None, ""]) is None

    def test_single_element(self):
        assert _list_to_str(["один"]) == "один"

    def test_integers_in_list(self):
        assert _list_to_str([1, 2, 3]) == "1, 2, 3"
