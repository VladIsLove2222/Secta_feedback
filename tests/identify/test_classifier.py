from classifier import classify


# --- not_found ---

class TestNotFound:

    def test_none_client(self):
        assert classify(None) == "not_found"

    def test_none_with_empty_tags(self):
        assert classify(None, []) == "not_found"

    def test_none_with_tags(self):
        assert classify(None, ["hardcore"]) == "not_found"


# --- hard (тег hardcore — высший приоритет) ---

class TestHardTag:

    def test_hard_overrides_loyal(self):
        client = {"discount": 10, "visits_count": 60}
        assert classify(client, ["hardcore"]) == "hard"

    def test_hard_overrides_client(self):
        client = {"discount": 0, "visits_count": 3}
        assert classify(client, ["hardcore"]) == "hard"

    def test_hard_overrides_newbie(self):
        client = {"discount": 0, "visits_count": 0}
        assert classify(client, ["hardcore"]) == "hard"

    def test_hard_among_other_tags(self):
        client = {"discount": 10, "visits_count": 60}
        assert classify(client, ["Сарафан", "hardcore", "VIP"]) == "hard"


# --- newbie (0 визитов, без тега hard) ---

class TestNewbie:

    def test_zero_visits_no_tag(self):
        client = {"discount": 0, "visits_count": 0}
        assert classify(client, []) == "newbie"

    def test_zero_visits_other_tags(self):
        client = {"discount": 0, "visits_count": 0}
        assert classify(client, ["Сарафан", "Новый"]) == "newbie"

    def test_zero_visits_none_tags(self):
        client = {"discount": 0, "visits_count": 0}
        assert classify(client, None) == "newbie"


# --- loyal (любая скидка > 0) ---

class TestLoyal:

    def test_loyal_discount_10(self):
        client = {"discount": 10, "visits_count": 60}
        assert classify(client, []) == "loyal"

    def test_loyal_discount_5(self):
        # скидка 5 теперь тоже loyal (нет типа regular)
        client = {"discount": 5, "visits_count": 20}
        assert classify(client, []) == "loyal"

    def test_loyal_discount_1(self):
        client = {"discount": 1, "visits_count": 3}
        assert classify(client, []) == "loyal"

    def test_loyal_discount_15(self):
        client = {"discount": 15, "visits_count": 60}
        assert classify(client, []) == "loyal"

    def test_loyal_with_unrelated_tags(self):
        client = {"discount": 10, "visits_count": 60}
        assert classify(client, ["Сарафан"]) == "loyal"


# --- client (найден, есть визиты, скидки нет) ---

class TestClient:

    def test_client_with_visits_no_discount(self):
        client = {"discount": 0, "visits_count": 3}
        assert classify(client, []) == "client"

    def test_client_one_visit(self):
        client = {"discount": 0, "visits_count": 1}
        assert classify(client, []) == "client"

    def test_client_many_visits_no_discount(self):
        client = {"discount": 0, "visits_count": 50}
        assert classify(client, []) == "client"


# --- Защита от None в данных клиента ---

class TestNoneSafety:

    def test_discount_none(self):
        # discount=None → 0 → client
        client = {"discount": None, "visits_count": 5}
        assert classify(client, []) == "client"

    def test_visits_none(self):
        # visits=None → 0 → newbie (даже при скидке)
        client = {"discount": 10, "visits_count": None}
        assert classify(client, []) == "newbie"

    def test_all_none(self):
        client = {"discount": None, "visits_count": None}
        assert classify(client, []) == "newbie"
