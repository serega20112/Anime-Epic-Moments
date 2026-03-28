from src.backend.domain.highlight.entity import Highlight
from src.backend.domain.highlight.policy import HighlightPolicy
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.services.recommendation_service import RecommendationService


class CreateHighlightUseCase:
    """
    Use case для создания Highlight
    """

    def __init__(
        self,
        repo: HighlightRepository,
        recommendation_service: RecommendationService | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service

    def execute(
        self,
        user_id: int | None,
        anime_id: int,
        episode: int,
        start_timestamp: float,
        end_timestamp: float,
        description: str = "",
        is_spoiler: bool = False,
        emotion: str | None = None,
        highlights_this_hour: int = 0,
    ) -> Highlight:
        """
        Создаёт новый Highlight с проверкой инвариантов и правил.
        Для гостей проверяется лимит добавлений в час.
        Запрещённый контент блокируется.
        """
        if not HighlightPolicy.can_add_highlight(user_id, highlights_this_hour):
            raise PermissionError("Превышен лимит добавления хайлайтов для гостя")

        if not HighlightPolicy.filter_spoiler_content(description):
            raise ValueError("Описание содержит запрещённый контент")

        highlight = Highlight(
            user_id=user_id,
            anime_id=anime_id,
            episode=episode,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            description=description,
            is_spoiler=is_spoiler,
            emotion=emotion,
        )

        result = self.repo.add(highlight)
        if self.recommendation_service and user_id is not None:
            self.recommendation_service.invalidate_user(int(user_id))
        return result
