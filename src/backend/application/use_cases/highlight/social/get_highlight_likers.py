from backend.application.interface.repositories.highlight_repository import HighlightRepository


class GetHighlightLikersUseCase:
    """Возвращает пользователей, поставивших лайк хайлайту."""

    def __init__(self, repo: HighlightRepository):
        self.repo = repo

    async def execute(self, highlight_id: int, limit: int = 20):
        return await self.repo.get_likers(
            highlight_id=highlight_id,
            limit=max(min(int(limit), 100), 1),
        )
