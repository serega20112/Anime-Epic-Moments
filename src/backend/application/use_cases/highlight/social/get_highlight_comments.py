from backend.application.interface.repositories.highlight_repository import HighlightRepository


class GetHighlightCommentsUseCase:
    """Возвращает комментарии к хайлайту с ограничением по размеру выборки."""

    def __init__(self, repo: HighlightRepository):
        self.repo = repo

    async def execute(self, highlight_id: int, limit: int = 20):
        return await self.repo.get_comments(
            highlight_id=highlight_id,
            limit=max(min(int(limit), 100), 1),
        )
