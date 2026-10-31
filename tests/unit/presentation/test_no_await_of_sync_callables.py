"""Защита от await над синхронными функциями проекта."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[3] / "src" / "backend"


def _definitions(tree: ast.AST) -> dict[str, bool]:
    """Собрать по дереву имена функций и классов с признаком корутины.

    Args:
        tree: Разобранное дерево модуля.

    Returns:
        dict[str, bool]: Имя -> определено ли оно как async-функция.
    """
    result: dict[str, bool] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            result[node.name] = True
        elif isinstance(node, ast.FunctionDef):
            result.setdefault(node.name, False)
        elif isinstance(node, ast.ClassDef):
            result.setdefault(node.name, False)
    return result


def _awaited_names(tree: ast.AST) -> list[tuple[int, str]]:
    """Перечислить имена вызовов, над которыми стоят await.

    Args:
        tree: Разобранное дерево модуля.

    Returns:
        list[tuple[int, str]]: Пары (номер строки, имя вызываемой сущности).
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Await) or not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        if isinstance(func, ast.Name):
            found.append((node.lineno, func.id))
        elif isinstance(func, ast.Attribute):
            found.append((node.lineno, func.attr))
    return found


def _collect_violations() -> list[str]:
    """Найти await над сущностями, которые во всём проекте только синхронные.

    Returns:
        list[str]: Описания нарушений в формате ``путь:строка имя``.
    """
    trees = {
        path: ast.parse(path.read_text(encoding="utf-8"))
        for path in sorted(BACKEND_ROOT.rglob("*.py"))
    }
    coroutine_names: dict[str, bool] = {}
    for tree in trees.values():
        for name, is_coroutine in _definitions(tree).items():
            coroutine_names[name] = coroutine_names.get(name, False) or is_coroutine

    violations: list[str] = []
    for path, tree in trees.items():
        for lineno, name in _awaited_names(tree):
            if coroutine_names.get(name) is False:
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{lineno} await {name}()")
    return violations


@pytest.mark.unit
def test_no_await_over_sync_callables() -> None:
    """Что тестируем: каждый await в backend вызывает корутину.

    Что передаём: исходники backend, разобранные как синтаксические деревья.
    Что ожидаем: ни один await не стоит над функцией, синхронной во всём проекте.
    """
    assert _collect_violations() == []


@pytest.mark.unit
def test_detector_flags_await_over_sync_function() -> None:
    """Что тестируем: сам детектор await над синхронной функцией.

    Что передаём: синтетический модуль, где await стоит над локальной sync-функцией.
    Что ожидаем: имя такой функции помечено как синхронное и попадает в список await.
    """
    tree = ast.parse("def plain():\n    return 1\n\nasync def run():\n    return await plain()\n")

    assert _definitions(tree) == {"plain": False, "run": True}
    assert _awaited_names(tree) == [(5, "plain")]
