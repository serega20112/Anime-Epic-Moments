"""Защита от вызова сценария любыми аргументами вместо Command/Query.

Все сценарии слоя application принимают один объект-намерение (U1). Роут,
вызвавший ``execute(user_id=...)`` после миграции сценария на Query-объект,
ломается только в рантайме — тесты страниц это не ловят, поэтому проверка
строится по исходникам слоя presentation.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PRESENTATION_ROOT = Path(__file__).resolve().parents[3] / "src" / "backend" / "presentation"
BUILDERS = ("map_", "build_")
SUFFIXES = ("Command", "Query")


def _is_intent_expression(node: ast.expr | None) -> bool:
    """Проверить, что выражение выглядит как объект намерения сценария.

    Args:
        node: Аргумент вызова ``execute`` либо None, если аргументов нет.

    Returns:
        bool: True для конструктора ``*Command``/``*Query``, билдера маппера или
            переменной с соответствующим именем.
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id
        return name.endswith(SUFFIXES) or name.startswith(BUILDERS)
    if isinstance(node, ast.Name):
        lowered = node.id.lower()
        return lowered.endswith(("command", "query")) or lowered in {"command", "query"}
    return False


def _collect_violations(tree: ast.AST, origin: str) -> list[str]:
    """Найти вызовы ``execute`` вне шаблона «один объект-намерение».

    Args:
        tree: Разобранное дерево модуля.
        origin: Имя файла для сообщения о нарушении.

    Returns:
        list[str]: Описания нарушений с номерами строк.
    """
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "execute":
            continue
        if node.args and _is_intent_expression(node.args[0]):
            continue
        if not node.args and not node.keywords:
            continue
        where = f"{origin}:{node.lineno}"
        if not node.args:
            violations.append(f"{where} execute только с именованными аргументами")
        else:
            violations.append(f"{where} execute принимает не Command/Query")
    return violations


def _scan_presentation() -> list[str]:
    """Пройти все модули presentation и собрать нарушения шаблона вызова.

    Returns:
        list[str]: Найденные нарушения по всем файлам слоя.
    """
    violations: list[str] = []
    for path in sorted(PRESENTATION_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        violations.extend(_collect_violations(tree, path.name))
    return violations


@pytest.mark.unit
def test_every_use_case_call_passes_intent_object() -> None:
    """Что тестируем: способ вызова сценариев из слоя маршрутов.
    Что передаём: исходники presentation, разобранные как синтаксические деревья.
    Что ожидаем: каждый ``execute`` вызывается с одним объектом Command/Query.
    """
    assert _scan_presentation() == []


@pytest.mark.unit
def test_detector_flags_keyword_call() -> None:
    """Что тестируем: сам детектор вызова с примитивами.
    Что передаём: синтетический модуль с ``execute(user_id=5)``.
    Что ожидаем: нарушение распознано и упомянут номер строки.
    """
    tree = ast.parse("async def run(uc):\n    return await uc.execute(user_id=5)\n")

    violations = _collect_violations(tree, "synthetic.py")

    assert violations == ["synthetic.py:2 execute только с именованными аргументами"]
