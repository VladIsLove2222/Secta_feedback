from app.classifier import classify


# --- not_found ---

class TestNotFound:

    def test_none_client(self):
        assert classify(None) == "not_found"

    def test_none_with_empty_tags(self):
        assert classify(None, []) == "not_found"

    def test_none_with_tags(self):
        # Даже если откуда-то пришли теги — клиент не найден
        assert classify(None, ["hardcore"]) == "not_found"


# --- hard (тег hardcore — высший приоритет) ---

class TestHardTag:

    def test_hard_overrides_loyal(self):
        client = {"discount": 10, "visits_count": 60}
        assert classify(client, ["hardcore"]) == "hard"

    def test_hard_overrides_regular(self):
        client = {"discount": 5, "visits_count": 20}
        assert classify(client, ["hardcore"]) == "hard"

    def test_hard_overrides_client(self):
        client = {"discount": 0, "visits_count": 3}
        assert classify(client, ["hardcore"]) == "hard"

    def test_hard_overrides_newbie(self):
        # Друг с 0 визитов всё равно идёт на жёсткую форму
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


# --- loyal (скидка 10%) ---

class TestLoyal:

    def test_loyal_no_tags(self):
        client = {"discount": 10, "visits_count": 60}
        assert classify(client, []) == "loyal"

    def test_loyal_with_unrelated_tags(self):
        client = {"discount": 10, "visits_count": 60}
        assert classify(client, ["Сарафан"]) == "loyal"

    def test_loyal_high_discount(self):
        # Любая скидка >= 10% считается loyal
        client = {"discount": 15, "visits_count": 60}
        assert classify(client, []) == "loyal"


# --- regular (скидка 5%) ---

class TestRegular:

    def test_regular_no_tags(self):
        client = {"discount": 5, "visits_count": 20}
        assert classify(client, []) == "regular"

    def test_regular_with_unrelated_tags(self):
        client = {"discount": 5, "visits_count": 20}
        assert classify(client, ["Через 4 недели"]) == "regular"


# --- client (найден, скидки нет, есть визиты) ---

class TestClient:

    def test_client_with_visits_no_discount(self):
        client = {"discount": 0, "visits_count": 3}
        assert classify(client, []) == "client"

    def test_client_one_visit(self):
        client = {"discount": 0, "visits_count": 1}
        assert classify(client, []) == "client"

    def test_client_many_visits_no_discount(self):
        # Много визитов без скидки — всё равно client (брат скидку не дал)
        client = {"discount": 0, "visits_count": 50}
        assert classify(client, []) == "client"


# --- Защита от None в данных клиента ---

class TestNoneSafety:

    def test_discount_none(self):
        client = {"discount": None, "visits_count": 5}
        # discount=None → 0, visits=5 → client
        assert classify(client, []) == "client"

    def test_visits_none(self):
        client = {"discount": 10, "visits_count": None}
        # visits=None → 0 → newbie (даже при скидке)
        assert classify(client, []) == "newbie"

    def test_all_none(self):
        client = {"discount": None, "visits_count": None}
        assert classify(client, []) == "newbie"
