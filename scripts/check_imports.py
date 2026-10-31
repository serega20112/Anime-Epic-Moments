"""Проверка границ слоёв без подготовки переменных окружения.

``lint-imports`` ищет пакет ``backend`` в ``sys.path`` и не находит его: исходники
лежат в ``src``, а не в корне репозитория. Поэтому команда ``uv run lint-imports``
без ``PYTHONPATH=src`` падает с сообщением
``Could not find package 'backend' in your Python path``. Скрипт добавляет каталог
``src`` в путь импорта сам, и проверка одинаково работает в любой ОС, в IDE и в CI.

Использование::

    uv run python scripts/check_imports.py

Возвращаемый код: 0 — все контракты выполнены, 1 — есть нарушение.
"""

from __future__ import annotations

import sys
from pathlib import Path

from importlinter.cli import lint_imports

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
CONFIG_PATH = PROJECT_ROOT / "pyproject.toml"


def main() -> int:
    """Проверить контракты import-linter и вернуть код завершения.

    Returns:
        int: 0, если все контракты выполнены, иначе 1.
    """
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))
    return int(lint_imports(config_filename=str(CONFIG_PATH)))


if __name__ == "__main__":
    raise SystemExit(main())
