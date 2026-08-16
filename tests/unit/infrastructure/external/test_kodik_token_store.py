from __future__ import annotations

import json

from backend.infrastructure.external.kodik_token_store import (
    KodikTokenStore,
    decrypt_token,
    encrypt_token,
)


def test_encrypt_decrypt_roundtrip_for_32_char_tokens():
    token = "9f3ab2c1d4e5f60718293a4b5c6d7e8f"
    obfuscated = encrypt_token(token)
    assert decrypt_token(obfuscated) == token


def test_encrypt_reverses_and_splits_parts():
    token = "1234567890abcdefghijklmnopqrstuv"
    obfuscated = encrypt_token(token)
    # p2[::-1] + p1[::-1]; длина p1=16
    assert len(obfuscated) == 2 * 24  # 2 * base64(16 байт)


def test_candidates_prefer_configured_token(tmp_path):
    token = "abcd" * 8  # 32 символа
    tokens_path = tmp_path / "tokens.json"
    tokens_path.write_text(
        json.dumps({"stable": [{"tokn": encrypt_token(token)}]}),
        encoding="utf-8",
    )
    store = KodikTokenStore(tokens_path=tokens_path, configured_token="configured")
    assert store.candidates() == ["configured", token]


def test_candidates_ignores_corrupt_tokens(tmp_path):
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
    assert store.candidates() == []


def test_missing_file_yields_empty_candidates(tmp_path):
    store = KodikTokenStore(tokens_path=tmp_path / "nope.json", configured_token=None)
    assert store.candidates() == []


def test_token_looks_invalid_on_russian_error_message():
    assert KodikTokenStore.token_looks_invalid({"error": "Отсутствует или неверный токен"})
    assert not KodikTokenStore.token_looks_invalid({"results": []})


def test_decrypt_uses_knowledge_of_parser_scheme():
    obfuscated = encrypt_token(token := "9f3ab2c1d4e5f60718293a4b5c6d7e8f")
    assert decrypt_token(obfuscated) == token
