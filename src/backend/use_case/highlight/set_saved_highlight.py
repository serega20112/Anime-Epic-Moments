from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache


class SetSavedHighlightUseCase:
    """Сохраняет или удаляет хайлайт из пользовательской коллекции."""

    def __init__(
        self,
        repo: HighlightRepository,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.repo = repo
        self.profile_overview_cache = profile_overview_cache

    def execute(self, highlight_id: int, user_id: int, saved: bool) -> bool:
        result = self.repo.set_saved(highlight_id=highlight_id, user_id=user_id, saved=saved)
        if self.profile_overview_cache is not None:
            self.profile_overview_cache.invalidate_overview(user_id)
        return result
