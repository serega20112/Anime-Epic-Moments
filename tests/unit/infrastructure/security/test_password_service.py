from __future__ import annotations

import pytest

from backend.infrastructure.security.password_service import PasswordService


@pytest.mark.unit
@pytest.mark.parametrize("password", ["password123", "AnimeEpicMoments!", "пароль-123"])
async def test_password_service_hashes_and_verifies_password(password):
    """Проверяем, что PasswordService хеширует пароль и затем успешно его проверяет."""
    service = PasswordService()

    hashed = await service.hash_password(password)

    assert hashed != password
    assert await service.verify_password(password, hashed) is True


@pytest.mark.unit
async def test_password_service_rejects_wrong_password():
    """Проверяем, что PasswordService возвращает False для неверного пароля."""
    service = PasswordService()
    hashed = await service.hash_password("correct-password")

    assert await service.verify_password("wrong-password", hashed) is False