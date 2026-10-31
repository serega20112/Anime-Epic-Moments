"""Сохранение черновика момента просмотра."""

from starlette import status

from backend.application.dto import SaveViewingMomentCommand
from backend.application.interface.repositories.moment_repository import MomentRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain import ViewingMoment


class SaveViewingMomentUseCase:
    """Создаёт или обновляет черновик момента просмотра."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий сохранения момента просмотра.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, command: SaveViewingMomentCommand) -> UseCaseResult:
        """Сохраняет момент просмотра внутри транзакции.

        Args:
            command: Команда сохранения момента просмотра.

        Returns:
            UseCaseResult: Результат с сохранённым моментом.
        """
        if command.moment_id is None and (command.episode <= 0 or command.timestamp < 0):
            return UseCaseResult.failure("invalid_moment", status_code=status.HTTP_400_BAD_REQUEST)
        moment = ViewingMoment(
            user_id=command.user_id,
            anime_id=command.anime_id,
            episode=command.episode,
            timestamp=command.timestamp,
            watch_source_id=command.watch_source_id,
            caption=command.caption,
            sticker=command.sticker,
            screenshot_url=command.screenshot_url,
            id=command.moment_id,
        )
        async with self._uow as uow:
            saved = await uow.repository(MomentRepository).save_moment(moment)
        return UseCaseResult.success(saved)
