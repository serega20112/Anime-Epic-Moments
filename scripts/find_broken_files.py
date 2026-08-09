"""Find Python files with syntax errors under src/."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"


def main() -> None:
    """Print paths of files with syntax errors.

    Returns:
        None
    """
    broken = []
    for path in SRC.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as error:
            broken.append((path, error.lineno, error.msg))
    for path, lineno, msg in broken:
        print(f"{path}:{lineno}: {msg}")
    print(f"Total broken files: {len(broken)}")


if __name__ == "__main__":
    main()