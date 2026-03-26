from src.backend.repository.highlight_repository import HighlightRepository


class DeleteHighlightUseCase:
    """
    Use case для удаления Highlight
    """

    def __init__(self, repo: HighlightRepository):
        self.repo = repo

    def execute(self, highlight_id: int):
        """
        Удаляет хайлайт по ID
        """
        highlight = self.repo.get_by_id(highlight_id)
        if not highlight:
            raise ValueError("Highlight не найден")
        self.repo.delete(highlight_id)
