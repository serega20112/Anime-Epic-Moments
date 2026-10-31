"""Сводка реакций на серию."""

from starlette import status

from backend.application.dto import GetEpisodeReactionsQuery
from backend.application.interface.repositories.reaction_repository import ReactionRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain.value_objects.reaction.reaction_summary import EpisodeReactionSummary


class GetEpisodeReactionsUseCase:
    """Агрегирует состояние реакций на серию для зрителей."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий получения реакций на серию.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, query: GetEpisodeReactionsQuery) -> UseCaseResult:
        """Считывает количество реакций и собственную реакцию зрителя.

        Args:
            query: Параметры запроса реакций.

        Returns:
            UseCaseResult: Агрегированное резюме реакций.
        """
        if query.episode <= 0:
            return UseCaseResult.failure("invalid_episode", status_code=status.HTTP_400_BAD_REQUEST)
        async with self._uow as uow:
            repo = uow.repository(ReactionRepository)
            counts = await repo.get_reaction_counts(query.anime_id, query.episode)
            user_reaction = None
            if query.user_id is not None:
                current = await repo.get_user_reaction(
                    query.user_id,
                    query.anime_id,
                    query.episode,
                )
                if current is not None:
                    user_reaction = current.reaction_type
        return UseCaseResult.success(
            EpisodeReactionSummary(counts=counts, user_reaction=user_reaction)
        )
