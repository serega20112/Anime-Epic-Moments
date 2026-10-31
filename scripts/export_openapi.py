"""Экспорт OpenAPI-схемы JSON API в репозиторий (этап 8, задачи M3 и M5).

Схема — контракт с мобильным клиентом: она хранится в репозитории и сравнивается
в тесте ``tests/unit/presentation/test_openapi_contract.py``, поэтому несовместимое
изменение ответа (пропавшее поле, другой тип, новая обязательная схема вместо
``Any``) роняет CI до выката, а не после.

Использование::

    uv run python scripts/export_openapi.py          # записать docs/api/openapi.json
    uv run python scripts/export_openapi.py --check  # проверить, что файл актуален

Возвращаемый код: 0 — успех, 1 — расхождение схемы с сохранённым файлом.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from backend.presentation.app_factory import create_app  # noqa: E402

SCHEMA_PATH = PROJECT_ROOT / "docs" / "api" / "openapi.json"
DRIFT_MESSAGE = "OpenAPI-схема разошлась с сохранённой в репозитории"


def render_schema() -> str:
    """Собрать JSON-текст OpenAPI-схемы приложения.

    Ключи упорядочены, чтобы правка маршрута не добавляла в diff шум от
    перестановки полей.

    Returns:
        str: Текст схемы с завершающим переводом строки.
    """
    schema = create_app().openapi() or {}
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def check_schema() -> int:
    """Сравнить сохранённую схему со сгенерированной.

    Returns:
        int: 0 при совпадении, 1 при расхождении или отсутствии файла.
    """
    if not SCHEMA_PATH.exists():
        print(f"{DRIFT_MESSAGE}: файл {SCHEMA_PATH.relative_to(PROJECT_ROOT)} отсутствует")
        return 1
    if SCHEMA_PATH.read_text(encoding="utf-8") != render_schema():
        print(f"{DRIFT_MESSAGE}: выполни uv run python scripts/export_openapi.py")
        return 1
    return 0


def write_schema() -> None:
    """Записать актуальную схему в файл репозитория."""
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(render_schema(), encoding="utf-8")
    print(f"схема записана в {SCHEMA_PATH.relative_to(PROJECT_ROOT)}")


def main(argv: list[str]) -> int:
    """Разобрать аргументы командной строки и выполнить команду.

    Args:
        argv: Аргументы после имени скрипта.

    Returns:
        int: Код завершения процесса.
    """
    if "--check" in argv:
        return check_schema()
    write_schema()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
