from __future__ import annotations

import pytest

from src.backend.repository.user_repository import UserRepository


def test_user_repository_is_abstract_and_declares_expected_methods():
    """Проверяем, что контракт UserRepository остается абстрактным и полным."""
    assert UserRepository.__abstractmethods__ == {
        "add",
        "get_by_email",
        "get_by_id",
        "update",
        "update_password",
    }

    with pytest.raises(TypeError):
        UserRepository()
