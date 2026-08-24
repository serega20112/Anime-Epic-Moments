from __future__ import annotations

import json

from backend.infrastructure.external.kodik_token_store import (
    KodikTokenStore,
    decrypt_token,
    encrypt_token,
)


async def test_encrypt_decrypt_roundtrip_for_32_char_tokens():
    token = "9f3ab2c1d4e5f60718293a4b5c6d7e8f"
    obfuscated = await encrypt_token(token)
    assert await decrypt_token(obfuscated) == token


async def test_encrypt_reverses_and_splits_parts():
    token = "1234567890abcdefghijklmnopqrstuv"
    obfuscated = await encrypt_token(token)
    assert len(obfuscated) == 2 * 24


async def test_candidates_prefer_configured_token(tmp_path):
    token = "abcd" * 8
    tokens_path = tmp_path / "tokens.json"
    tokens_path.write_text(
        json.dumps({"stable": [{"tokn": await encrypt_token(token)}]}),
        encoding="utf-8",
    )
    store = KodikTokenStore(tokens_path=tokens_path, configured_token="configured")
    assert await store.candidates() == ["configured", token]


async def test_candidates_ignores_corrupt_tokens(tmp_path):
    tokens_path = tmp_path / "tokens.json"
    tokens_path.write_text(
        json.dumps(
            {
                "stable": [
                    {"tokn": "not-valid-base64!?"},
                ],
            }
        ),
        encoding="utf-8",
    )
    store = KodikTokenStore(tokens_path=tokens_path, configured_token=None)
    assert await store.candidates() == []


async def test_missing_file_yields_empty_candidates(tmp_path):
    store = KodikTokenStore(tokens_path=tmp_path / "nope.json", configured_token=None)
    assert await store.candidates() == []


async def test_token_looks_invalid_on_russian_error_message():
    assert await KodikTokenStore.token_looks_invalid({"error": "Отсутствует или неверный токен"})
    assert not await KodikTokenStore.token_looks_invalid({"results": []})


async def test_decrypt_uses_knowledge_of_parser_scheme():
    obfuscated = await encrypt_token(token := "9f3ab2c1d4e5f60718293a4b5c6d7e8f")
    assert await decrypt_token(obfuscated) == token
