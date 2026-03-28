from src.backend.repository.highlight_repository import HighlightRepository


class SetSavedHighlightUseCase:
    """Сохраняет или удаляет хайлайт из пользовательской коллекции."""

    def __init__(self, repo: HighlightRepository):
        self.repo = repo

    def execute(self, highlight_id: int, user_id: int, saved: bool) -> bool:
        return self.repo.set_saved(highlight_id=highlight_id, user_id=user_id, saved=saved)
