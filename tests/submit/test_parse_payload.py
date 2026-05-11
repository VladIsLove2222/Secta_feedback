import json
import uuid
from submit_index import _parse_payload


# --- Базовые поля ---

class TestParsePayloadBase:

    def test_form_type_extracted(self):
        body = {"type": "loyal", "answers": {"nps": "9"}}
        row = _parse_payload(body)
        assert row["$form_type"] == "loyal"

    def test_unknown_type_stored(self):
        body = {"type": "unknown_form", "answers": {}}
        row = _parse_payload(body)
        assert row["$form_type"] == "unknown_form"

    def test_missing_type_defaults_to_unknown(self):
        body = {"answers": {"nps": "9"}}
        row = _parse_payload(body)
        assert row["$form_type"] == "unknown"

    def test_id_is_uuid(self):
        body = {"type": "loyal", "answers": {}}
        row = _parse_payload(body)
        uuid.UUID(row["$id"])  # бросит ValueError если не UUID

    def test_created_at_is_int(self):
        body = {"type": "loyal", "answers": {}}
        row = _parse_payload(body)
        assert isinstance(row["$created_at"], int)
        assert row["$created_at"] > 0

    def test_answers_stored_as_json_string(self):
        answers = {"nps": "9", "agree": "yes"}
        body = {"type": "loyal", "answers": answers}
        row = _parse_payload(body)
        assert json.loads(row["$answers"]) == answers


# --- NPS ---

class TestNps:

    def test_nps_parsed(self):
        body = {"type": "loyal", "answers": {"nps": "9"}}
        row = _parse_payload(body)
        assert row["$nps_score"] == 9

    def test_nps_missing_is_none(self):
        body = {"type": "loyal", "answers": {}}
        row = _parse_payload(body)
        assert row["$nps_score"] is None

    def test_nps_non_numeric_is_none(self):
        body = {"type": "loyal", "answers": {"nps": "хорошо"}}
        row = _parse_payload(body)
        assert row["$nps_score"] is None


# --- Hidden fields из params ---

class TestHiddenFieldsFromParams:

    def test_name_and_master_from_params(self):
        body = {
            "type": "loyal",
            "params": {"name": "Иван", "master": "Костя"},
            "answers": {},
        }
        row = _parse_payload(body)
        assert row["$client_name"] == "Иван"
        assert row["$master_name"] == "Костя"

    def test_master_fallback_to_answers(self):
        body = {
            "type": "hard",
            "answers": {"master": "Дима"},
        }
        row = _parse_payload(body)
        assert row["$master_name"] == "Дима"

    def test_params_stored_as_json(self):
        body = {
            "type": "loyal",
            "params": {"name": "Иван", "visits": "10"},
            "answers": {},
        }
        row = _parse_payload(body)
        stored = json.loads(row["$params"])
        assert stored["name"] == "Иван"

    def test_no_params_no_hidden_in_answers(self):
        body = {"type": "newbie", "answers": {"nps": "8"}}
        row = _parse_payload(body)
        assert row["$client_name"] is None


# --- Типы форм ---

class TestFormTypes:

    def test_hard_form(self):
        body = {
            "type": "hard",
            "params": {"name": "Иван", "master": "Костя"},
            "answers": {
                "nps": "10",
                "master_work": "5",
                "master_human": "5",
                "agree": "yes",
            },
        }
        row = _parse_payload(body)
        assert row["$form_type"] == "hard"
        assert row["$nps_score"] == 10
        assert row["$master_work"] == 5
        assert row["$master_human"] == 5
        assert row["$agree"] == "yes"

    def test_loyal_form(self):
        body = {
            "type": "loyal",
            "params": {"name": "Сергей", "master": "Вова", "visits": "30"},
            "answers": {
                "nps": "9",
                "master_work": "4",
                "dont-change": "всё нравится",
                "nps-improve-7-8": "чуть быстрее",
            },
        }
        row = _parse_payload(body)
        assert row["$form_type"] == "loyal"
        assert row["$nps_score"] == 9
        assert row["$dont_change"] == "всё нравится"
        assert row["$nps_improve_7_8"] == "чуть быстрее"

    def test_client_form(self):
        body = {
            "type": "client",
            "params": {"name": "Дмитрий"},
            "answers": {
                "nps": "7",
                "how_found": "Instagram",
                "plan_return": "yes",
                "admin_rating": "5",
            },
        }
        row = _parse_payload(body)
        assert row["$how_found"] == "Instagram"
        assert row["$plan_return"] == "yes"
        assert row["$admin_rating"] == 5

    def test_newbie_form(self):
        body = {
            "type": "newbie",
            "answers": {
                "nps": "8",
                "how_found": "Сарафан",
                "service_done": "Стрижка",
                "waited": "no",
                "warned": "yes",
            },
        }
        row = _parse_payload(body)
        assert row["$form_type"] == "newbie"
        assert row["$how_found"] == "Сарафан"
        assert row["$service_done"] == "Стрижка"
        assert row["$waited"] == "no"
        assert row["$warned"] == "yes"

    def test_accomp_form(self):
        body = {
            "type": "accomp",
            "answers": {
                "who_waiting": "жена",
                "merch_want": "yes",
                "merch_buy": "no",
                "atmosphere": "5",  # ключ в API — "atmosphere", не "atmosphere_rating"
            },
        }
        row = _parse_payload(body)
        assert row["$who_waiting"] == "жена"
        assert row["$merch_want"] == "yes"
        assert row["$merch_buy"] == "no"
        assert row["$atmosphere_rating"] == 5

    def test_regular_anon_form(self):
        body = {
            "type": "regular_anon",
            "answers": {
                "nps": "6",
                "nps-improve-low": "хочу скидку",
                "contact_back": "yes",
            },
        }
        row = _parse_payload(body)
        assert row["$form_type"] == "regular_anon"
        assert row["$nps_score"] == 6
        assert row["$nps_improve_low"] == "хочу скидку"
        assert row["$contact_back"] == "yes"


# --- Массивы ---

class TestArrayFields:

    def test_master_bad_reasons_array(self):
        body = {"type": "loyal", "answers": {"master_bad_reasons": ["опоздал", "порезал"]}}
        row = _parse_payload(body)
        assert row["$master_bad_reasons"] == "опоздал, порезал"

    def test_money_array(self):
        body = {"type": "loyal", "answers": {"money": ["дорого", "нет акций"]}}
        row = _parse_payload(body)
        assert row["$money"] == "дорого, нет акций"

    def test_new_services_array(self):
        body = {"type": "client", "answers": {"new_services": ["маникюр", "спа"]}}
        row = _parse_payload(body)
        assert row["$new_services"] == "маникюр, спа"

    def test_empty_array_becomes_none(self):
        body = {"type": "loyal", "answers": {"master_bad_reasons": []}}
        row = _parse_payload(body)
        assert row["$master_bad_reasons"] is None

    def test_missing_array_field_is_none(self):
        body = {"type": "loyal", "answers": {}}
        row = _parse_payload(body)
        assert row["$master_bad_reasons"] is None
        assert row["$money"] is None


# --- Matrix ---

class TestMatrixField:

    def test_matrix_all_fields(self):
        body = {
            "type": "loyal",
            "answers": {
                "matrix": {
                    "cleanness": "5",
                    "music": "4",
                    "smell": "5",
                    "comfort": "4",
                    "coffee": "3",
                }
            },
        }
        row = _parse_payload(body)
        assert row["$m_cleanness"] == 5
        assert row["$m_music"] == 4
        assert row["$m_smell"] == 5
        assert row["$m_comfort"] == 4
        assert row["$m_coffee"] == 3

    def test_matrix_partial_fields(self):
        body = {"type": "loyal", "answers": {"matrix": {"cleanness": "5"}}}
        row = _parse_payload(body)
        assert row["$m_cleanness"] == 5
        assert row["$m_music"] is None

    def test_no_matrix_all_none(self):
        body = {"type": "loyal", "answers": {}}
        row = _parse_payload(body)
        assert row["$m_cleanness"] is None
        assert row["$m_coffee"] is None


# --- Дефисные ключи ---

class TestHyphenKeys:

    def test_notif_disturb_which(self):
        body = {"type": "loyal", "answers": {"notif-disturb-which": "смс"}}
        row = _parse_payload(body)
        assert row["$notif_disturb_which"] == "смс"

    def test_nps_improve_idiot(self):
        body = {"type": "loyal", "answers": {"nps-improve-idiot": "всё плохо"}}
        row = _parse_payload(body)
        assert row["$nps_improve_idiot"] == "всё плохо"

    def test_admin_bad_text(self):
        body = {"type": "loyal", "answers": {"admin-bad-text": "нагрубил"}}
        row = _parse_payload(body)
        assert row["$admin_bad_text"] == "нагрубил"

    def test_dont_change(self):
        body = {"type": "loyal", "answers": {"dont-change": "всё отлично"}}
        row = _parse_payload(body)
        assert row["$dont_change"] == "всё отлично"
