"""Automatically add Google-style docstrings to public code elements."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"


def _summary(node: ast.AST, kind: str, name: str) -> str:
    """Build a summary line for an AST node.

    Args:
        node: AST node.
        kind: Element kind.
        name: Element name.

    Returns:
        str: Summary text.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
        suffix = f" with arguments {', '.join(args)}." if args else "."
        return f"{kind.capitalize()} {name}{suffix}"
    return f"{kind.capitalize()} {name}."


def _docstring(node: ast.AST, kind: str, name: str) -> str:
    """Build a Google-style docstring for an element.

    Args:
        node: AST node.
        kind: Element kind.
        name: Element name.

    Returns:
        str: Formatted docstring.
    """
    summary = _summary(node, kind, name)
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return f'"""{summary}"""'
    parts = [summary]
    args = [a for a in node.args.args if a.arg not in ("self", "cls")]
    if args:
        parts.append("")
        parts.append("    Args:")
        for arg in args:
            annotation = ast.unparse(arg.annotation) if arg.annotation else ""
            parts.append(f"        {arg.arg}: {annotation}: Parameter description.")
    returns = node.returns
    if returns is not None and ast.unparse(returns) != "None":
        parts.append("")
        parts.append("    Returns:")
        parts.append(f"        {ast.unparse(returns)}: Return value description.")
    return '"""' + "\n".join(parts) + '"""'


def process_file(file_path: Path) -> int:
    """Add missing docstrings to one file.

    Args:
        file_path: Python file to process.

    Returns:
        int: Number of inserted docstrings.
    """
    source = file_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    for parent_node in ast.walk(tree):
        for child in ast.iter_child_nodes(parent_node):
            child.parent = parent_node
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            if ast.get_docstring(node) is None:
                missing.append((node, "class"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            parent = getattr(node, "parent", None)
            if ast.get_docstring(node) is None:
                kind = "method" if isinstance(parent, ast.ClassDef) else "function"
                missing.append((node, kind))
    if not missing:
        return 0
    lines = source.split("\n")
    for node, kind in sorted(missing, key=lambda item: item[0].lineno, reverse=True):
        source_line = lines[node.lineno - 1]
        indent = source_line[: len(source_line) - len(source_line.lstrip())]
        insert_at = node.end_lineno
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            insert_at = node.end_lineno
        text = _docstring(node, kind, node.name)
        block = "\n".join(f"{indent}{line}" if line else "" for line in text.split("\n"))
        lines.insert(insert_at, block)
        for idx in range(insert_at + 1, len(lines) + 1):
            pass
        source = "\n".join(lines)
        lines = source.split("\n")
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(missing)


def main() -> None:
    """Process all Python files under src/.

    Returns:
        None
    """
    total = 0
    for path in SRC.rglob("*.py"):
        total += process_file(path)
    print(f"Added {total} docstrings.")


if __name__ == "__main__":
    main()