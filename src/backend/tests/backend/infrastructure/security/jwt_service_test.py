from __future__ import annotations

import jwt
import pytest

from src.backend.infrastructure.security import jwt_service as jwt_service_module
from src.backend.infrastructure.security.jwt_service import ALGORITHM, JWTService


def test_jwt_service_creates_and_decodes_access_token(monkeypatch):
    """Проверяем, что JWTService создает access token и извлекает из него user_id."""
    monkeypatch.setattr(jwt_service_module.Settings, "secret_key", "test-secret")
    monkeypatch.setattr(jwt_service_module.Settings, "access_token_expire_minutes", 30)
    service = JWTService()

    token = service.create_token(user_id=17)

    assert service.decode_token(token) == 17


def test_jwt_service_creates_and_decodes_refresh_token(monkeypatch):
    """Проверяем, что JWTService создает refresh token и извлекает из него user_id."""
    monkeypatch.setattr(jwt_service_module.Settings, "secret_key", "test-secret")
    monkeypatch.setattr(jwt_service_module.Settings, "refresh_token_expire_days", 15)
    service = JWTService()

    token = service.create_refresh_token(user_id=23)

    assert service.decode_refresh_token(token) == 23


@pytest.mark.parametrize(
    ("token_type", "decoder"),
    [
        ("password_reset", "decode_token"),
        ("access", "decode_password_reset_token"),
        ("access", "decode_refresh_token"),
        ("refresh", "decode_token"),
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


def test_jwt_service_returns_positive_ttl_for_fresh_token(monkeypatch):
    """Проверяем, что JWTService умеет вычислять оставшийся TTL токена."""
    monkeypatch.setattr(jwt_service_module.Settings, "secret_key", "test-secret")
    monkeypatch.setattr(jwt_service_module.Settings, "access_token_expire_minutes", 1)
    service = JWTService()

    token = service.create_access_token(user_id=5)

    assert service.get_token_ttl_seconds(token, expected_type="access") > 0
