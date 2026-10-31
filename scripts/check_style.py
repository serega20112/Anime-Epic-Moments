"""Проверка стилевого стандарта кода ``src/backend``.

Требования заказчика (пункт 1.1 ТЗ) шире того, что умеет ruff: докстринг
обязан быть на русском, а объяснений в ``#``-комментариях быть не должно.
Ruff проверяет наличие и форму докстрингов (D) и подсказывает комментарии
с подсказками предков (ERA001), но «русская ли строка» и «не строка ли это
под капотом тулзы» решает этот скрипт.

Проверяются два правила:

1. В ``src/backend`` нет ``#``-комментариев, кроме служебных директив
   инструментов (``# noqa``, ``# type:``, ``# fmt:``, ``# ruff:``).
2. У каждого модуля, класса, функции и метода есть докстринг с кириллицей
   (кроме тривиальных приватных функций и перегрузок ``@overload``).

Использование::

    uv run python scripts/check_style.py

Выходит с ненулевым кодом, если найдены нарушения; список печатается построчно.
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOT = Path("src/backend")
ALLOWED_DIRECTIVES = ("noqa", "type:", "fmt:", "ruff:", "isort:", "pragma:")
TRIVIAL_NAMES = {"__init__", "__repr__", "__str__"}
DECORATOR_NAMES = {"overload", "property", "setter", "deleter", "cached_property"}


@dataclass(frozen=True, slots=True)
class Violation:
    """Найденное нарушение стилевого стандарта.

    Attributes:
        path: Путь к файлу.
        line: Номер строки.
        rule: Код правила (``COMMENT`` или ``DOCSTRING``).
        message: Что не так и как это исправить.
    """

    path: Path
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        """Вернуть строку отчёта в формате ``путь:строка: [правило] текст``.

        Returns:
            str: Готовая к печати строка.
        """
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


def is_allowed_comment(text: str) -> bool:
    """Проверить, является ли комментарий служебной директивой инструмента.

    Args:
        text: Текст комментария вместе с ``#``.

    Returns:
        bool: True для директив, которые стандарт разрешает.
    """
    body = text.lstrip("#").strip().lower()
    return any(body.startswith(directive) for directive in ALLOWED_DIRECTIVES)


def find_hash_comments(path: Path) -> list[Violation]:
    """Найти запрещённые ``#``-комментарии в файле.

    Разбор через ``tokenize`` гарантирует, что строки с решёткой внутри
    текстовых литералов (URL, примеры команд) не считаются комментариями.

    Args:
        path: Путь к Python-файлу.

    Returns:
        list[Violation]: Найденные комментарии-нарушения.
    """
    source = path.read_text(encoding="utf-8")
    violations: list[Violation] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return [
            Violation(
                path=path,
                line=1,
                rule="COMMENT",
                message="файл не разбирается токенизатором — проверить вручную",
            )
        ]
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        if is_allowed_comment(token.string):
            continue
        violations.append(
            Violation(
                path=path,
                line=token.start[0],
                rule="COMMENT",
                message=f"объяснение в комментарии несут в докстринг: {token.string.strip()}",
            )
        )
    return violations


def _is_private(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Определить тривиальную приватную функцию, освобождаемую от докстринга.

    Приватная функция без тела сложнее одной инструкции считается
    нетривиальной: именно такие функции и нужно объяснять.

    Args:
        node: Узел функции.

    Returns:
        bool: True, если докстринг не требуется.
    """
    if not node.name.startswith("_") or node.name in TRIVIAL_NAMES:
        return False
    return len(node.body) <= 1


def _has_exempt_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Проверить, помечена ли функция декоратором, не требующим докстринга.

    Args:
        node: Узел функции.

    Returns:
        bool: True для перегрузок и свойства-геттера.
    """
    for decorator in node.decorator_list:
        name = getattr(decorator, "id", None) or getattr(decorator, "attr", None)
        if name in DECORATOR_NAMES:
            return True
    return False


def find_missing_docstrings(path: Path) -> list[Violation]:
    """Найти объявления без докстринга и докстринги без кириллицы.

    Args:
        path: Путь к Python-файлу.

    Returns:
        list[Violation]: Список найденных отступлений от стандарта.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    violations: list[Violation] = []

    module_doc = ast.get_docstring(tree)
    if module_doc is None:
        violations.append(
            Violation(path=path, line=1, rule="DOCSTRING", message="нет докстринга модуля")
        )
    elif not _has_cyrillic(module_doc):
        violations.append(
            Violation(path=path, line=1, rule="DOCSTRING", message="докстринг модуля не на русском")
        )

    for node in ast.walk(tree):
        violations.extend(_check_node_doc(path, node))
    return violations


def _check_node_doc(path: Path, node: ast.AST) -> list[Violation]:
    """Проверить докстринг одного узла класса или функции.

    Args:
        path: Путь к файлу для отчёта.
        node: Узел дерева разбора.

    Returns:
        list[Violation]: Пустой список либо одно нарушение узла.
    """
    if not isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
        return []
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        if _is_private(node) or _has_exempt_decorator(node):
            return []
    doc = ast.get_docstring(node)
    label = f"{node.__class__.__name__.replace('Def', '')} {node.name}"
    if doc is None:
        return [
            Violation(
                path=path, line=node.lineno, rule="DOCSTRING", message=f"нет докстринга: {label}"
            )
        ]
    if not _has_cyrillic(doc):
        return [
            Violation(
                path=path,
                line=node.lineno,
                rule="DOCSTRING",
                message=f"докстринг не на русском: {label}",
            )
        ]
    return []


def _has_cyrillic(text: str) -> bool:
    """Проверить наличие хотя бы одной кириллической буквы в тексте.

    Args:
        text: Проверяемый текст.

    Returns:
        bool: True, если текст содержит кириллицу.
    """
    return any("\u0400" <= char <= "\u04ff" for char in text)


def collect_violations(root: Path = SOURCE_ROOT) -> list[Violation]:
    """Собрать нарушения по всем Python-файлам указанного корня.

    Args:
        root: Каталог, который проверяется целиком.

    Returns:
        list[Violation]: Отсортированные по файлам и строкам нарушения.
    """
    violations: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        violations.extend(find_hash_comments(path))
        violations.extend(find_missing_docstrings(path))
    return violations


def main() -> int:
    """Напечатать отчёт и вернуть код завершения для CI.

    Returns:
        int: 0 при чистом коде, 1 при найденных нарушениях.
    """
    violations = collect_violations()
    for violation in violations:
        print(violation)
    comments = sum(1 for item in violations if item.rule == "COMMENT")
    docstrings = sum(1 for item in violations if item.rule == "DOCSTRING")
    print(
        f"\ncheck-style: комментариев {comments}, докстрингов {docstrings}, всего {len(violations)}"
    )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
