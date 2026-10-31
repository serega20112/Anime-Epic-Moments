"""Сценарий публикации черновика момента как хайлайта."""

from starlette import status

from backend.application.dto import CreateHighlightCommand, PublishViewingMomentCommand
from backend.application.interface.repositories.moment_repository import MomentRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.result import UseCaseResult
from backend.domain import ViewingMoment

MOMENT_WINDOW_SECONDS = 15.0


class PublishViewingMomentUseCase:
    """Опубликовывает черновик момента просмотра как хайлайт."""

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        create_highlight: CreateHighlightUseCase,
    ) -> None:
        """Инициализирует сценарий публикации момента просмотра.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
            create_highlight: Сценарий создания хайлайта из черновика.
        """
        self._uow = uow
        self._create_highlight = create_highlight

    async def execute(self, command: PublishViewingMomentCommand) -> UseCaseResult:
        """Опубликовывает момент просмотра как хайлайт внутри транзакции.

        Args:
            command: Команда публикации момента просмотра.

        Returns:
            UseCaseResult: Результат с созданным хайлайтом.
        """
        async with self._uow as uow:
            repository = uow.repository(MomentRepository)
            moment = await repository.get_moment(command.moment_id, command.user_id)
            if moment is None:
                return UseCaseResult.failure(
                    "moment_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
            highlight_result = await self._create_highlight.execute(
                self._build_highlight_command(command, moment)
            )
            if not highlight_result.ok:
                return UseCaseResult.failure(
                    str(highlight_result.error or "publish_failed"),
                    status_code=highlight_result.status_code,
                )
            await repository.delete_moment(moment.id, command.user_id)
            return UseCaseResult.success(highlight_result.data, status_code=status.HTTP_201_CREATED)

    def _build_highlight_command(
        self, command: PublishViewingMomentCommand, moment: ViewingMoment
    ) -> CreateHighlightCommand:
        """Собрать команду создания хайлайта по границам окна момента.

        Args:
            command: Команда публикации момента.
            moment: Черновик момента просмотра.

        Returns:
            CreateHighlightCommand: Команда создания хайлайта.
        """
        half_window = MOMENT_WINDOW_SECONDS / 2
        return CreateHighlightCommand(
            user_id=command.user_id,
            anime_id=moment.anime_id,
            episode=moment.episode,
            start_timestamp=max(0.0, moment.timestamp - half_window),
            end_timestamp=moment.timestamp + half_window,
            title=command.title or moment.caption or f"Момент {moment.episode} серии",
            category=command.category or moment.sticker,
            description=command.description or "",
            is_spoiler=command.is_spoiler,
            emotion=command.emotion,
        )
