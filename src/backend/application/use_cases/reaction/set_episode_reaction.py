"""Постановка и смена реакции на серию."""

from starlette import status

from backend.application.dto import SetEpisodeReactionCommand
from backend.application.interface.repositories.reaction_repository import ReactionRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain import EpisodeReaction, EpisodeReactionType
from backend.domain.value_objects.reaction.reaction_summary import EpisodeReactionSummary


class SetEpisodeReactionUseCase:
    """Устанавливает или удаляет реакцию пользователя на серию."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий установки реакции.

        Args:
            uow: Единица работы, задающая границу транзакции.
        """
        self._uow = uow

    async def execute(self, command: SetEpisodeReactionCommand) -> UseCaseResult:
        """Применяет реакцию и возвращает обновлённое состояние серии.

        Args:
            command: Команда установки или удаления реакции.

        Returns:
            UseCaseResult: Результат с обновлённым резюме реакций.
        """
        if command.episode <= 0:
            return UseCaseResult.failure("invalid_episode", status_code=status.HTTP_400_BAD_REQUEST)

        reaction_type = EpisodeReactionType.from_value(command.reaction_type)
        if command.liked and reaction_type is None:
            return UseCaseResult.failure(
                "invalid_reaction_type", status_code=status.HTTP_400_BAD_REQUEST
            )

        async with self._uow as uow:
            repo = uow.repository(ReactionRepository)
            if not command.liked:
                await repo.remove_reaction(
                    command.user_id,
                    command.anime_id,
                    command.episode,
                )
            else:
                await repo.set_reaction(
                    EpisodeReaction(
                        user_id=command.user_id,
                        anime_id=command.anime_id,
                        episode=command.episode,
                        reaction_type=reaction_type,
                        timestamp=command.timestamp,
                    )
                )

            counts = await repo.get_reaction_counts(command.anime_id, command.episode)
            current = await repo.get_user_reaction(
                command.user_id,
                command.anime_id,
                command.episode,
            )

        return UseCaseResult.success(
            EpisodeReactionSummary(
                counts=counts,
                user_reaction=current.reaction_type if current else None,
            )
        )
