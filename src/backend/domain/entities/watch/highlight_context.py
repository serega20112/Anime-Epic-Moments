from datetime import datetime


class HighlightContext:
    def __init__(
        self,
        highlight_id: int,
        watch_source_id: int,
        translation_id: int,
        title: str = "",
        id: int | None = None,
        created_at: datetime | None = None,
        original_title: str | None = None,
    ):
        self.id = id
        self.highlight_id = highlight_id
        self.watch_source_id = watch_source_id
        self.translation_id = translation_id
        self.title = title
        self.created_at = created_at or datetime.utcnow()
        self.original_title = original_title
