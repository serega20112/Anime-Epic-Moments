"""Remove docstrings incorrectly inserted at the end of code blocks."""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"

_BROKEN_START = re.compile(r'^\s*"""(Class|Method|Function) ')


def fix_file(file_path: Path) -> int:
    """Remove broken docstrings from a single file.

    Args:
        file_path: Python file to fix.

    Returns:
        int: Number of removed docstring blocks.
    """
    lines = file_path.read_text(encoding="utf-8").split("\n")
    result: list[str] = []
    removed = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        if _BROKEN_START.match(line):
            removed += 1
            index += 1
            while index < len(lines) and '"""' not in lines[index]:
                index += 1
            if index < len(lines):
                index += 1
            continue
        result.append(line)
        index += 1
    file_path.write_text("\n".join(result).rstrip("\n") + "\n", encoding="utf-8")
    return removed


def main() -> None:
    """Fix all broken docstrings under src/.

    Returns:
        None
    """
    total = 0
    for path in SRC.rglob("*.py"):
        total += fix_file(path)
    print(f"Removed {total} broken docstring blocks.")


if __name__ == "__main__":
    main()