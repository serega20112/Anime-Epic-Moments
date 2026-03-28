from __future__ import annotations

import pytest

from src.backend.repository.highlight_repository import HighlightRepository


def test_highlight_repository_is_abstract_and_declares_expected_methods():
    """Проверяем, что контракт HighlightRepository остается абстрактным и полным."""
    assert HighlightRepository.__abstractmethods__ == {
        "add",
        "update",
        "delete",
        "get_by_id",
        "get_by_user",
        "get_public_top",
        "get_by_anime_episode",
    }

    with pytest.raises(TypeError):
        HighlightRepository()
