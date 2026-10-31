"""Инструмент сборки baseline-списка нарушений границ слоёв.

Контракт ``Presentation does not reach Infrastructure`` в ``pyproject.toml``
содержит временный список ``ignore_imports``: по мере переезда импортов
строки из него удаляются, а
``docs/01-architecture/importlinter-baseline.md`` остаётся точной картой
оставшихся нарушений.

Скрипт перечитывает ``src/backend/presentation`` и печатает блок
``ignore_imports = [...]`` для вставки в ``pyproject.toml`` — так список не
расходится с кодом из-за ручной правки.

Использование::

    uv run python scripts/export_importlinter_baseline.py
"""

from __future__ import annotations

import ast
from pathlib import Path

PRESENTATION_ROOT = Path("src/backend/presentation")
FORBIDDEN_PREFIX = "backend.infrastructure"


def _module_name(path: Path) -> str:
    """Преобразовать путь файла в имя модула пакета backend.

    Args:
        path: Путь к .py-файлу внутри ``src/backend``.

    Returns:
        str: Точечное имя модуля, например
            ``backend.presentation.api.v1.anime_route``.
    """
    relative = path.relative_to(Path("src"))
    return ".".join(relative.with_suffix("").parts)


def _direct_imports(path: Path) -> set[str]:
    """Собрать целевые модули, которые файл импортирует напрямую.

    Args:
        path: Путь к .py-файлу слоя presentation.

    Returns:
        set[str]: Имена запрещённых модулей назначения.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.update(
                alias.name for alias in node.names if alias.name.startswith(FORBIDDEN_PREFIX)
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(FORBIDDEN_PREFIX):
                targets.add(module)
    return targets


def collect_violations() -> list[tuple[str, str]]:
    """Собрать все прямые нарушения ``presentation -> infrastructure``.

    Returns:
        list[tuple[str, str]]: Пары «модуль-источник, модуль-цель»,
            отсортированные для стабильного вывода.
    """
    pairs: set[tuple[str, str]] = set()
    for path in sorted(PRESENTATION_ROOT.rglob("*.py")):
        source = _module_name(path)
        for target in _direct_imports(path):
            pairs.add((source, target))
    return sorted(pairs)


def main() -> None:
    """Напечатать пару строк для каждого нарушения в формате import-linter."""
    for source, target in collect_violations():
        print(f'    "{source} -> {target}",')


if __name__ == "__main__":
    main()
