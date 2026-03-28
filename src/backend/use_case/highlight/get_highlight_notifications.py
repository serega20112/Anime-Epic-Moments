from src.backend.repository.highlight_repository import HighlightRepository


class GetHighlightNotificationsUseCase:
    """Возвращает простые уведомления по реакциям на хайлайты пользователя."""

    def __init__(self, repo: HighlightRepository):
        self.repo = repo

    def execute(self, user_id: int, limit: int = 20):
        return self.repo.get_recent_activity(user_id=user_id, limit=max(min(int(limit), 100), 1))
