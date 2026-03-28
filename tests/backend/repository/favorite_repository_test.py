from __future__ import annotations

import pytest

from src.backend.repository.favorite_repository import FavoriteRepository


def test_favorite_repository_is_abstract_and_declares_expected_methods():
    """Проверяем, что контракт FavoriteRepository остается абстрактным и полным."""
    assert FavoriteRepository.__abstractmethods__ == {
        "add",
        "remove",
        "get_by_user",
    }

    with pytest.raises(TypeError):
        FavoriteRepository()
