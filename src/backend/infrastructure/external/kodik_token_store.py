"""Kodik public token store and obfuscation helpers.

Kodik-экосистема использует публичные токены, которые распространяются
в зашифрованном виде (файл ``kdk_tokns/tokens.json``), чтобы их нельзя было
найти через поисковые системы. Здесь реализовано обратимое шифрование/дешифрование
ровно по той схеме, которую использует официальный парсер Kodik, плюс выбор
рабочего токена с проверкой на живом API.
"""

from __future__ import annotations

import asyncio
import json
import re
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Any

_SECTION_ORDER = ("stable", "unstable", "legacy")
_TOKEN_ERROR_HINTS = (
    "неверный токен",
    "отсутствует",
    "доступ запрещён",
    "invalid token",
)


async def encrypt_token(token: str) -> str:
    """Зашифровать токен по схеме Kodik-парсера.

    Первая половина кодируется в base64, вторая — тоже, затем части
    реверсируются и склеиваются (обратный порядок частей).

    Args:
        token: Исходный токен.

    Returns:
        str: Зашифрованное представление.
    """
    first_idx = 16
    p1 = b64encode(token[:first_idx].encode("utf-8")).decode("utf-8")
    p2 = b64encode(token[first_idx:].encode("utf-8")).decode("utf-8")
    return p2[::-1] + p1[::-1]


async def decrypt_token(obfuscated: str) -> str:
    """Расшифровать токен, сохранённый функцией :func:`encrypt_token`.

    Args:
        obfuscated: Зашифрованный токен.

    Returns:
        str: Исходный токен.
    """
    midpoint = len(obfuscated) // 2
    p1 = obfuscated[:midpoint][::-1]
    p2 = obfuscated[midpoint:][::-1]
    p1_text = b64decode(p1.encode("utf-8")).decode("utf-8")
    p2_text = b64decode(p2.encode("utf-8")).decode("utf-8")
    return p2_text + p1_text


class KodikTokenStore:
    """Загружает зашифрованные публичные токены Kodik и выбирает рабочий.

    Токен, заданный через ``configured_token``, имеет приоритет. Если он не
    проходит проверку (или не задан), перебираются расшифрованные токены из
    ``tokens.json`` (разделы stable → unstable → legacy).
    """

    def __init__(
        self,
        tokens_path: str | Path,
        configured_token: str | None = None,
    ):
        self.tokens_path = Path(tokens_path)
        self.configured_token = configured_token or None

    async def _read_encrypted_tokens(self) -> list[str]:
        """Прочитать и расшифровать токены из файла ``tokens.json``."""
        try:
            payload = await asyncio.to_thread(self._load_tokens_file)
        except (OSError, ValueError, TypeError):
            return []

        tokens: list[str] = []
        for section in _SECTION_ORDER:
            entries = payload.get(section) or []
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                obfuscated = entry.get("tokn")
                if not obfuscated:
                    continue
                token = await self._safe_decrypt(str(obfuscated))
                if token:
                    tokens.append(token)
        return tokens

    def _load_tokens_file(self) -> dict[str, Any]:
        """Load the raw tokens payload from disk (sync I/O helper)."""
        with self.tokens_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    async def candidates(self) -> list[str]:
        """Все токены-кандидаты в порядке приоритета.

        Returns:
            list[str]: configured_token первым, затем расшифрованные публичные.
        """
        ordered: list[str] = []
        if self.configured_token:
            ordered.append(self.configured_token)
        for token in await self._read_encrypted_tokens():
            if token not in ordered:
                ordered.append(token)
        return ordered

    async def _safe_decrypt(self, obfuscated: str) -> str:
        try:
            return await decrypt_token(obfuscated)
        except (ValueError, UnicodeDecodeError, TypeError):
            return ""

    @staticmethod
    async def token_looks_invalid(payload: Any) -> bool:
        """True, когда ответ API явно сообщает о неверном токене."""
        if not isinstance(payload, dict):
            return False
        error = payload.get("error") or payload.get("message") or ""
        if isinstance(error, str):
            lowered = error.lower()
            if any(hint in lowered for hint in _TOKEN_ERROR_HINTS):
                return True
        return bool(re.search(r"токен", str(error), re.IGNORECASE))
