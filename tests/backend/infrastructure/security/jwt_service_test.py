from __future__ import annotations

import jwt
import pytest

from src.backend.infrastructure.security import jwt_service as jwt_service_module
from src.backend.infrastructure.security.jwt_service import ALGORITHM, JWTService


def test_jwt_service_creates_and_decodes_access_token(monkeypatch):
    """Проверяем, что JWTService создает access token и извлекает из него user_id."""
    monkeypatch.setattr(jwt_service_module.Settings, "secret_key", "test-secret")
    service = JWTService()

    token = service.create_token(user_id=17)

    assert service.decode_token(token) == 17


@pytest.mark.parametrize(
    ("token_type", "decoder"),
    [
        ("password_reset", "decode_token"),
        ("access", "decode_password_reset_token"),
    ],
)
def test_jwt_service_rejects_unexpected_token_type(token_type, decoder, monkeypatch):
    """Проверяем, что JWTService отклоняет токены неподходящего типа."""
    monkeypatch.setattr(jwt_service_module.Settings, "secret_key", "test-secret")
    service = JWTService()
    token = jwt.encode(
        {"user_id": 1, "token_type": token_type},
        "test-secret",
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.InvalidTokenError):
        getattr(service, decoder)(token)


def test_jwt_service_creates_and_decodes_password_reset_token(monkeypatch):
    """Проверяем, что JWTService создает и валидирует password reset token."""
    monkeypatch.setattr(jwt_service_module.Settings, "secret_key", "test-secret")
    service = JWTService()

    token = service.create_password_reset_token(user_id=33, expires_minutes=15)

    assert service.decode_password_reset_token(token) == 33
