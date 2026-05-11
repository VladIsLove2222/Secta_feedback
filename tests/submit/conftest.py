import importlib.util
import os
import sys
from unittest.mock import MagicMock

# Мокаем ydb до того как index.py его импортирует
sys.modules.setdefault("ydb", MagicMock())
sys.modules.setdefault("ydb.iam", MagicMock())

os.environ.setdefault("YDB_ENDPOINT", "grpcs://test-endpoint")
os.environ.setdefault("YDB_DATABASE", "/test/db")

SUBMIT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "functions", "submit")
)
sys.path.insert(0, SUBMIT_DIR)

# Загружаем под уникальным именем — избегаем коллизии с functions/identify/index.py
spec = importlib.util.spec_from_file_location(
    "submit_index", os.path.join(SUBMIT_DIR, "index.py")
)
_submit_index_mod = importlib.util.module_from_spec(spec)
sys.modules["submit_index"] = _submit_index_mod
spec.loader.exec_module(_submit_index_mod)
