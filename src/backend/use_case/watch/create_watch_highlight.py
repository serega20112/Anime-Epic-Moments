from src.backend.domain.watch.entity import HighlightContext
from src.backend.repository.watch_repository import WatchRepository
from src.backend.use_case.highlight.create_highlight import CreateHighlightUseCase


class CreateWatchHighlightUseCase:
    """Создает хайлайт из плеера и сохраняет его playback context."""

    def __init__(
        self,
        create_highlight_use_case: CreateHighlightUseCase,
        watch_repo: WatchRepository,
    ):
        self.create_highlight_use_case = create_highlight_use_case
        self.watch_repo = watch_repo

    def execute(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
        title: str,
        start_timestamp: float,
        end_timestamp: float,
        description: str,
        is_spoiler: bool,
        emotion: str | None,
        watch_source_id: int,
        translation_id: int,
    ):
        highlight = self.create_highlight_use_case.execute(
            user_id=user_id,
            anime_id=anime_id,
            episode=episode,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            description=description,
            is_spoiler=is_spoiler,
            emotion=emotion,
        )
        self.watch_repo.add_highlight_context(
            HighlightContext(
                highlight_id=highlight.id or 0,
                watch_source_id=watch_source_id,
                translation_id=translation_id,
                title=title,
            )
        )
        return highlight
