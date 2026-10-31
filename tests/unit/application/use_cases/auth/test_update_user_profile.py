from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import UpdateProfileCommand
from backend.application.use_cases.auth.profile.update_user_profile import (
    UpdateUserProfileUseCase,
)
from backend.domain import User
from tests.support.fakes import FakeUnitOfWork


def _user(*, username: str = "tester") -> User:
    """Собрать пользователя профиля с указанной темой и статусом."""
    return User(
        id=4,
        email="user@example.com",
        username=username,
        password_hash="hashed",
        avatar_url="https://example.com/old.png",
        created_at=datetime(2026, 3, 20),
    )


def _command(**overrides) -> UpdateProfileCommand:
    """Собрать команду правки профиля с переопределёнными полями."""
    fields = {
        "user_id": 4,
        "username": "  new-name  ",
        "avatar_url": " https://example.com/new.png ",
        "status": "  ",
        "show_watch_activity": False,
        "show_recent_episodes": True,
    }
    fields.update(overrides)
    return UpdateProfileCommand(**fields)


def _use_case(*, user) -> tuple:
    """Собрать сценарий правки профиля с двойниками репозитория и кэша."""
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = user
    user_repository.update.side_effect = lambda item: item
    profile_cache = AsyncMock()
    uow = FakeUnitOfWork(UserRepository=user_repository)
    return UpdateUserProfileUseCase(uow, profile_cache), uow, user_repository, profile_cache


@pytest.mark.unit
class TestUpdateUserProfileUseCase:
    """Юнит-тесты обновления профиля пользователя."""

    async def test_updates_fields_and_invalidates_cache(self):
        """Что тестируем: сохранение нормализованных полей профиля.
        Что передаём: имя и аватар с пробелами, пустой статус.
        Что ожидаем: поля обновлены, пустой статус сведён к None, кэш очищен.
        """
        use_case, uow, users, profile_cache = _use_case(user=_user())

        result = await use_case.execute(_command())

        assert result.ok is True
        assert result.data.username == "new-name"
        assert result.data.avatar_url == "https://example.com/new.png"
        assert result.data.status is None
        assert result.data.show_watch_activity is False
        assert result.data.show_recent_episodes is True
        assert uow.commits == 1
        users.update.assert_awaited_once()
        profile_cache.invalidate_overview.assert_awaited_once_with(4)

    async def test_rejects_empty_username_before_database(self):
        """Что тестируем: отказ при пустом имени пользователя.
        Что передаём: username из пробелов.
        Что ожидаем: отказ, база и кэш не затронуты.
        """
        use_case, _uow, users, profile_cache = _use_case(user=_user())

        result = await use_case.execute(_command(username="   "))

        assert result.ok is False
        assert result.error_message == "Имя пользователя не может быть пустым"
        assert result.error_endpoint == "auth.profile_page"
        users.get_by_id.assert_not_awaited()
        profile_cache.invalidate_overview.assert_not_awaited()

    async def test_rejects_unknown_user(self):
        """Что тестируем: отказ при отсутствующем пользователе.
        Что передаём: репозиторий возвращает None.
        Что ожидаем: отказ на страницу профиля, сохранение не выполняется.
        """
        use_case, _uow, users, profile_cache = _use_case(user=None)

        result = await use_case.execute(_command())

        assert result.ok is False
        assert result.error_message == "Пользователь не найден"
        users.update.assert_not_awaited()
        profile_cache.invalidate_overview.assert_not_awaited()

    async def test_rejects_username_forbidden_by_aggregate(self):
        """Что тестируем: отклонение имени, нарушающего инварианты агрегата.
        Что передаём: слишком длинное имя пользователя.
        Что ожидаем: отказ с текстом агрегата, профиль не сохранён, транзакция откачена.
        """
        use_case, uow, users, profile_cache = _use_case(user=_user())

        result = await use_case.execute(_command(username="x" * 40))

        assert result.ok is False
        assert "Username" in result.error_message
        assert uow.commits == 1
        users.update.assert_not_awaited()
        profile_cache.invalidate_overview.assert_not_awaited()
