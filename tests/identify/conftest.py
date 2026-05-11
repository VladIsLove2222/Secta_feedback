import importlib.util
import os
import sys

os.environ.setdefault("YCLIENTS_PARTNER_TOKEN", "test-partner")
os.environ.setdefault("YCLIENTS_USER_TOKEN", "test-user")
os.environ.setdefault("YCLIENTS_COMPANY_ID", "99999")

IDENTIFY_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "functions", "identify")
)
# Добавляем в sys.path до загрузки модуля — его импорты (classifier, config, ...) идут через sys.path
sys.path.insert(0, IDENTIFY_DIR)

# Загружаем под уникальным именем — избегаем коллизии с functions/submit/index.py
spec = importlib.util.spec_from_file_location(
    "identify_index", os.path.join(IDENTIFY_DIR, "index.py")
)
_identify_index_mod = importlib.util.module_from_spec(spec)
sys.modules["identify_index"] = _identify_index_mod
spec.loader.exec_module(_identify_index_mod)
