"""Comprehensive migration script to restructure the codebase to Clean Architecture.

Moves all source files to the target structure defined in the ТЗ, updates all
import paths across the entire codebase, restructures tests, removes ``#``
comments (except ``# NOTE:``), and creates the required ``__init__.py`` packages.
"""

from __future__ import annotations

import os
import re
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "src")

IMPORT_REPLACEMENTS: list[tuple[str, str]] = [
    ("src.backend.dependencies.settings", "src.config.settings"),
    ("src.backend.dependencies.container", "src.infrastructure.di.container"),
    (
        "src.backend.dependencies.auth_dependencies",
        "src.presentation.dependencies.auth_dependencies",
    ),
    ("from src.backend.dependencies import container", "from src.infrastructure.di import container"),
    ("from src.backend.dependencies import settings", "from src.config import settings"),
    ("src.backend.create_app", "src.presentation.app_factory"),
    ("src.backend.delivery", "src.presentation"),
    ("src.backend.use_case", "src.application.use_cases"),
    ("src.backend.services", "src.application.services"),
    ("src.backend.repository", "src.domain.repositories"),
    ("src.backend.infrastructure", "src.infrastructure"),
    ("src.backend.domain", "src.domain"),
]

SOURCE_MOVES: list[tuple[str, str]] = [
    ("src/backend/domain", "src/domain"),
    ("src/backend/use_case", "src/application/use_cases"),
    ("src/backend/services", "src/application/services"),
    ("src/backend/repository", "src/domain/repositories"),
    ("src/backend/infrastructure", "src/infrastructure"),
    ("src/backend/delivery", "src/presentation"),
    ("src/backend/create_app.py", "src/presentation/app_factory.py"),
    ("src/backend/dependencies/settings.py", "src/config/settings.py"),
    ("src/backend/dependencies/container.py", "src/infrastructure/di/container.py"),
    (
        "src/backend/dependencies/auth_dependencies.py",
        "src/presentation/dependencies/auth_dependencies.py",
    ),
]

TEST_RENAMES: list[tuple[str, str]] = [
    ("tests/backend/delivery", "tests/presentation"),
    ("tests/backend/use_case", "tests/application/use_cases"),
    ("tests/backend/services", "tests/application/services"),
    ("tests/backend/repository", "tests/domain/repositories"),
    ("tests/backend/infrastructure", "tests/infrastructure"),
    ("tests/backend/domain", "tests/domain"),
]

TEST_FILE_MOVES: list[tuple[str, str]] = [
    ("tests/backend/create_app_test.py", "tests/presentation/app_factory_test.py"),
    ("tests/backend/dependencies/settings_test.py", "tests/config/settings_test.py"),
    ("tests/backend/dependencies/container_test.py", "tests/infrastructure/di/container_test.py"),
    (
        "tests/backend/dependencies/auth_dependencies_test.py",
        "tests/presentation/dependencies/auth_dependencies_test.py",
    ),
]

NEW_DIRS = [
    "src/application",
    "src/application/use_cases",
    "src/application/services",
    "src/config",
    "src/domain",
    "src/domain/repositories",
    "src/events",
    "src/infrastructure",
    "src/infrastructure/di",
    "src/presentation",
    "src/presentation/dependencies",
    "src/utils",
    "tests",
    "tests/application",
    "tests/application/use_cases",
    "tests/application/services",
    "tests/config",
    "tests/domain",
    "tests/domain/repositories",
    "tests/infrastructure",
    "tests/infrastructure/di",
    "tests/presentation",
    "tests/presentation/dependencies",
]

COMMENT_PATTERN = re.compile(r'^(\s*)#(?!\s*NOTE:)(?!\s*noqa)(?!\s*type:)(?!\s*pragma:)(?!\s*pylint:)(?!\s*ruff:).*$',
                             re.MULTILINE)
BLANK_COMMENT_PATTERN = re.compile(r'\n\s*#\s*\n')


def _move(src_rel: str, dst_rel: str) -> None:
    """Move a file or directory from *src_rel* to *dst_rel* relative to BASE."""
    src_path = os.path.join(BASE, src_rel.replace("/", os.sep))
    dst_path = os.path.join(BASE, dst_rel.replace("/", os.sep))
    if not os.path.exists(src_path):
        print(f"SKIP (not found): {src_rel}")
        return
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    if os.path.exists(dst_path):
        if os.path.isdir(dst_path):
            shutil.rmtree(dst_path)
        else:
            os.remove(dst_path)
    shutil.move(src_path, dst_path)
    print(f"MOVED: {src_rel} -> {dst_rel}")


def _update_imports_in_file(file_path: str) -> bool:
    """Replace all old import paths in *file_path*. Returns True if changed."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False

    original = content
    for old, new in IMPORT_REPLACEMENTS:
        content = content.replace(old, new)

    if content != original:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def _strip_comments_in_file(file_path: str) -> bool:
    """Remove ``#`` comments (except ``# NOTE:``, noqa, type:, pragma:, etc.)."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False

    original = content
    content = COMMENT_PATTERN.sub("", content)
    for _ in range(5):
        new_content = BLANK_COMMENT_PATTERN.sub("\n", content)
        if new_content == content:
            break
        content = new_content

    lines = []
    prev_blank = False
    for line in content.splitlines():
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        lines.append(line)
        prev_blank = is_blank
    content = "\n".join(lines)
    if content and not content.endswith("\n"):
        content += "\n"

    if content != original:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def _create_init_files() -> None:
    """Create ``__init__.py`` files in all source and test packages."""
    for root in [SRC, os.path.join(BASE, "tests")]:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if "__pycache__" in dirpath:
                continue
            init_path = os.path.join(dirpath, "src/__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, "w", encoding="utf-8") as f:
                    f.write('"""Package init."""\n')
                print(f"CREATED: {os.path.relpath(init_path, BASE)}")


def _update_all_imports() -> None:
    """Update import paths in all Python files under src/ and tests/."""
    changed = 0
    for root in [SRC, os.path.join(BASE, "tests")]:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            if "__pycache__" in dirpath:
                continue
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                file_path = os.path.join(dirpath, filename)
                if _update_imports_in_file(file_path):
                    changed += 1
    print(f"Updated imports in {changed} files")


def _strip_all_comments() -> None:
    """Remove ``#`` comments from all Python files under src/ and tests/."""
    changed = 0
    for root in [SRC, os.path.join(BASE, "tests")]:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            if "__pycache__" in dirpath:
                continue
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                file_path = os.path.join(dirpath, filename)
                if _strip_comments_in_file(file_path):
                    changed += 1
    print(f"Stripped comments in {changed} files")


def _move_tests() -> None:
    """Move tests from src/backend/tests to top-level tests/."""
    src_tests = os.path.join(BASE, "src", "backend", "tests")
    dst_tests = os.path.join(BASE, "tests")
    if os.path.isdir(src_tests):
        if os.path.exists(dst_tests):
            shutil.rmtree(dst_tests)
        shutil.move(src_tests, dst_tests)
        print("MOVED: src/backend/tests -> tests")

    for old_rel, new_rel in TEST_RENAMES:
        old_path = os.path.join(BASE, old_rel.replace("/", os.sep))
        new_path = os.path.join(BASE, new_rel.replace("/", os.sep))
        if os.path.isdir(old_path):
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            if os.path.exists(new_path):
                shutil.rmtree(new_path)
            shutil.move(old_path, new_path)
            print(f"RENAMED: {old_rel} -> {new_rel}")

    for old_rel, new_rel in TEST_FILE_MOVES:
        old_path = os.path.join(BASE, old_rel.replace("/", os.sep))
        new_path = os.path.join(BASE, new_rel.replace("/", os.sep))
        if os.path.isfile(old_path):
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            shutil.move(old_path, new_path)
            print(f"MOVED: {old_rel} -> {new_rel}")

    backend_tests_dir = os.path.join(BASE, "tests", "backend")
    if os.path.isdir(backend_tests_dir):
        remaining = os.listdir(backend_tests_dir)
        if not remaining or all(item in ("__init__.py",) for item in remaining):
            shutil.rmtree(backend_tests_dir)
            print("REMOVED: tests/backend (empty)")


def _cleanup_backend() -> None:
    """Remove the now-empty src/backend directory."""
    backend_dir = os.path.join(BASE, "src", "backend")
    if os.path.isdir(backend_dir):
        shutil.rmtree(backend_dir, ignore_errors=True)
        print("REMOVED: src/backend")


def _create_new_dirs() -> None:
    """Create all required target directories."""
    for dir_rel in NEW_DIRS:
        dir_path = os.path.join(BASE, dir_rel.replace("/", os.sep))
        os.makedirs(dir_path, exist_ok=True)
    print("Created target directories")


def _verify_structure() -> None:
    """Print the final src/ structure for verification."""
    print("\n=== Final src/ structure ===")
    for item in sorted(os.listdir(SRC)):
        full = os.path.join(SRC, item)
        tag = "[DIR]" if os.path.isdir(full) else "[FILE]"
        print(f"  {tag} {item}")

    tests_dir = os.path.join(BASE, "tests")
    if os.path.isdir(tests_dir):
        print("\n=== Final tests/ structure ===")
        for item in sorted(os.listdir(tests_dir)):
            full = os.path.join(tests_dir, item)
            tag = "[DIR]" if os.path.isdir(full) else "[FILE]"
            print(f"  {tag} {item}")


def main() -> None:
    """Run the full migration: move, update imports, strip comments, init files."""
    print("=== Step 1: Create target directories ===")
    _create_new_dirs()

    print("\n=== Step 2: Move source files ===")
    for src_rel, dst_rel in SOURCE_MOVES:
        _move(src_rel, dst_rel)

    print("\n=== Step 3: Move tests ===")
    _move_tests()

    print("\n=== Step 4: Cleanup src/backend ===")
    _cleanup_backend()

    print("\n=== Step 5: Update import paths ===")
    _update_all_imports()

    print("\n=== Step 6: Strip # comments ===")
    _strip_all_comments()

    print("\n=== Step 7: Create __init__.py files ===")
    _create_init_files()

    print("\n=== Step 8: Verify structure ===")
    _verify_structure()

    print("\n=== Migration complete ===")


if __name__ == "__main__":
    main()
