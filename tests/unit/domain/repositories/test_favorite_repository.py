from __future__ import annotations

from backend.domain.repositories.favorite_repository import FavoriteRepository


class TestFavoriteRepository:
    def test_abstract_method_names(self):
        assert {"add", "remove", "get_by_user"} <= set(FavoriteRepository.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            FavoriteRepository()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
