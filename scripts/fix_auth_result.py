"""Remove await from AuthResult.success/failure calls (now sync)."""

import pathlib
import re

USE_CASES = pathlib.Path("src/backend/application/use_cases/auth")
changed = 0
for path in USE_CASES.rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(
        r"return await (AuthResult\.(?:success|failure)\()",
        r"return \1",
        text,
    )
    new_text = re.sub(
        r"= await (AuthResult\.(?:success|failure)\()",
        r"= \1",
        new_text,
    )
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        changed += 1
        print("patched", path)
print("files changed:", changed)