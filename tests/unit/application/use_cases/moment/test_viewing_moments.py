from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import (
    PublishViewingMomentCommand,
    SaveViewingMomentCommand,
)
from backend.application.use_cases import (
    DeleteViewingMomentUseCase,
    GetUserViewingMomentsUseCase,
    PublishViewingMomentUseCase,
    SaveViewingMomentUseCase,
)
from backend.domain import ViewingMoment


@pytest.mark.unit
class TestSaveViewingMomentUseCase:
    """Юнит-тесты создания/обновления чернового момента."""

    async def test_creates_moment(self):
        """Что тестируем: создание момента из команды.
        Что передаём: валидные episode и timestamp.
        Что ожидаем: момент сохранён, результат успешен.
        """
        moment_repo = AsyncMock()
        moment_repo.save_moment.return_value = SimpleMoment(id=1, user_id=1)
        use_case = SaveViewingMomentUseCase(moment_repo, AsyncMock())

        result = await use_case.execute(
            SaveViewingMomentCommand(user_id=1, anime_id=9, episode=2, timestamp=12.5)
        )

        assert result.ok is True
        assert result.data.id == 1
        moment = moment_repo.save_moment.await_args.args[0]
        assert isinstance(moment, ViewingMoment)
        assert moment.episode == 2

    async def test_rejects_invalid_new_moment(self):
        """Что тестируем: отказ при невалидном новом моменте.
        Что передаём: episode = 0, moment_id = None.
        Что ожидаем: failure со статусом 400.
        """
        moment_repo = AsyncMock()
        use_case = SaveViewingMomentUseCase(moment_repo, AsyncMock())

        result = await use_case.execute(
            SaveViewingMomentCommand(user_id=1, anime_id=9, episode=0, timestamp=1.0)
        )

        assert result.ok is False
        assert result.status_code == 400
        moment_repo.save_moment.assert_not_awaited()


@pytest.mark.unit
class TestPublishViewingMomentUseCase:
    """Юнит-тесты публикации момента как хайлайта."""

    async def test_publishes_and_deletes_moment(self):
        """Что тестируем: публикацию момента в хайлайт.
        Что передаём: существующий момент и замоканный create_highlight.
        Что ожидаем: хайлайт создан, момент удалён.
        """
        moment_repo = AsyncMock()
        moment_repo.get_moment.return_value = SimpleMoment(
            id=5,
            user_id=1,
            anime_id=9,
            episode=2,
            timestamp=10.0,
            caption="Ого",
        )
        create_highlight = AsyncMock()
        create_highlight.execute.return_value = SimpleResult(ok=True, data=SimpleMoment(id=99))
        use_case = PublishViewingMomentUseCase(moment_repo, create_highlight, AsyncMock())

        result = await use_case.execute(
            PublishViewingMomentCommand(user_id=1, moment_id=5, is_spoiler=False)
        )

        assert result.ok is True
        assert result.data.id == 99
        command = create_highlight.execute.await_args.args[0]
        assert command.anime_id == 9
        assert command.episode == 2
        assert command.title == "Ого"
        assert command.start_timestamp == 2.5
        assert command.end_timestamp == 17.5
        moment_repo.delete_moment.assert_awaited_once_with(5, 1)

    async def test_missing_moment_returns_not_found(self):
        """Что тестируем: отсутствующий момент.
        Что передаём: moment_id без записи в репозитории.
        Что ожидаем: failure со статусом 404.
        """
        moment_repo = AsyncMock()
        moment_repo.get_moment.return_value = None
        create_highlight = AsyncMock()
        use_case = PublishViewingMomentUseCase(moment_repo, create_highlight, AsyncMock())

        result = await use_case.execute(
            PublishViewingMomentCommand(user_id=1, moment_id=404, is_spoiler=False)
        )

        assert result.ok is False
        assert result.status_code == 404
        create_highlight.execute.assert_not_awaited()


@pytest.mark.unit
class TestGetUserViewingMomentsUseCase:
    """Юнит-тесты получения списка моментов."""

    async def test_returns_moments(self):
        """Что тестируем: возврат списка моментов пользователя.
        Что передаём: замоканный репозиторий со списком.
        Что ожидаем: результат успешен, данные — список.
        """
        moment_repo = AsyncMock()
        moment_repo.get_moments_by_user.return_value = [SimpleMoment(id=1), SimpleMoment(id=2)]
        use_case = GetUserViewingMomentsUseCase(moment_repo)

        result = await use_case.execute(1)

        assert result.ok is True
        assert len(result.data) == 2
        moment_repo.get_moments_by_user.assert_awaited_once_with(1)


@pytest.mark.unit
class TestDeleteViewingMomentUseCase:
    """Юнит-тесты удаления момента."""

    async def test_deletes_existing_moment(self):
        """Что тестируем: удаление существующего момента.
        Что передаём: момент, который есть в репозитории.
        Что ожидаем: результат успешен.
        """
        moment_repo = AsyncMock()
        moment_repo.delete_moment.return_value = True
        use_case = DeleteViewingMomentUseCase(moment_repo, AsyncMock())

        result = await use_case.execute(5, 1)

        assert result.ok is True
        moment_repo.delete_moment.assert_awaited_once_with(5, 1)

    async def test_missing_moment_returns_not_found(self):
        """Что тестируем: отсутствующий момент.
        Что передаём: момент, которого нет.
        Что ожидаем: failure со статусом 404.
        """
        moment_repo = AsyncMock()
        moment_repo.delete_moment.return_value = False
        use_case = DeleteViewingMomentUseCase(moment_repo, AsyncMock())

        result = await use_case.execute(404, 1)

        assert result.ok is False
        assert result.status_code == 404


class SimpleMoment:
    """Минимальный заменитель ViewingMoment для тестов."""

    def __init__(self, id=None, user_id=1, anime_id=9, episode=2, timestamp=10.0, caption=None):
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = episode
        self.timestamp = timestamp
        self.caption = caption
        self.sticker = None


class SimpleResult:
    """Минимальный заменитель результата use case."""

    def __init__(self, ok=True, data=None, status_code=201, error=None):
        self.ok = ok
        self.data = data
        self.status_code = status_code
        self.error = error
