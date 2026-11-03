from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto.account import DeleteAccountCommand, ExportUserDataQuery
from backend.application.use_cases.account import DeleteAccountUseCase, ExportUserDataUseCase
from backend.domain import User
from tests.support.fakes import FakeUnitOfWork


def _user() -> User:
    """Собрать пользователя для сценариев аккаунта."""
    return User(
        id=7,
        email="owner@example.com",
        username="owner",
        password_hash="hash",
        status="in a band",
    )


@pytest.mark.unit
class TestDeleteAccountUseCase:
    """Юнит-тесты удаления аккаунта."""

    async def test_deletes_user_and_invalidates_cache(self):
        """Что тестируем: успешное удаление аккаунта и сброс кэша.
        Что передаём: репозиторий, сообщивший об удалении строки.
        Что ожидаем: результат успех с deleted, кэш профиля сброшен.
        """
        user_repository = AsyncMock()
        user_repository.delete.return_value = True
        profile_cache = AsyncMock()
        uow = FakeUnitOfWork(UserRepository=user_repository)

        result = await DeleteAccountUseCase(uow, profile_cache).execute(
            DeleteAccountCommand(user_id=7)
        )

        assert result.ok is True
        assert result.data == {"deleted": True}
        profile_cache.invalidate_overview.assert_awaited_once_with(7)

    async def test_returns_not_found_when_user_missing(self):
        """Что тестируем: удаление отсутствующего аккаунта.
        Что передаём: репозиторий, ничего не удаливший.
        Что ожидаем: отказ 404, кэш не сбрасывается.
        """
        user_repository = AsyncMock()
        user_repository.delete.return_value = False
        profile_cache = AsyncMock()
        uow = FakeUnitOfWork(UserRepository=user_repository)

        result = await DeleteAccountUseCase(uow, profile_cache).execute(
            DeleteAccountCommand(user_id=7)
        )

        assert result.ok is False
        assert result.status_code == 404
        profile_cache.invalidate_overview.assert_not_awaited()


@pytest.mark.unit
class TestExportUserDataUseCase:
    """Юнит-тесты выгрузки данных пользователя."""

    async def test_collects_all_sections(self):
        """Что тестируем: сборку разделов выгрузки из репозиториев.
        Что передаём: профиль, одно избранное, статус, хайлайт и коллекцию.
        Что ожидаем: словарь с пятью разделами и корректными полями.
        """
        user_repository = AsyncMock()
        user_repository.get_by_id.return_value = _user()
        favorite_repository = AsyncMock()
        favorite_repository.get_by_user.return_value = [
            SimpleNamespace(anime_id=185, title="Initial D")
        ]
        watch_repository = AsyncMock()
        watch_repository.get_statuses_by_user.return_value = [
            SimpleNamespace(anime_id=185, status="watching", current_episode=3, rating=None)
        ]
        highlight_repository = AsyncMock()
        highlight_repository.get_by_user.return_value = [
            SimpleNamespace(id=9, anime_id=185, episode=1, title="Moment")
        ]
        collection_repository = AsyncMock()
        collection_repository.get_user_collections.return_value = [
            SimpleNamespace(id=2, title="Favourites", is_public=True)
        ]
        uow = FakeUnitOfWork(
            UserRepository=user_repository,
            FavoriteRepository=favorite_repository,
            WatchRepository=watch_repository,
            HighlightRepository=highlight_repository,
            CollectionRepository=collection_repository,
        )

        result = await ExportUserDataUseCase(uow).execute(ExportUserDataQuery(user_id=7))

        assert result.ok is True
        data = result.data
        assert data["profile"]["username"] == "owner"
        assert data["favorites"] == [{"anime_id": 185, "title": "Initial D"}]
        assert data["statuses"][0]["current_episode"] == 3
        assert data["highlights"][0]["id"] == 9
        assert data["collections"][0]["is_public"] is True

    async def test_returns_not_found_when_user_missing(self):
        """Что тестируем: выгрузку для отсутствующего пользователя.
        Что передаём: профиль не найден.
        Что ожидаем: отказ 404.
        """
        user_repository = AsyncMock()
        user_repository.get_by_id.return_value = None
        uow = FakeUnitOfWork(UserRepository=user_repository)

        result = await ExportUserDataUseCase(uow).execute(ExportUserDataQuery(user_id=7))

        assert result.ok is False
        assert result.status_code == 404
