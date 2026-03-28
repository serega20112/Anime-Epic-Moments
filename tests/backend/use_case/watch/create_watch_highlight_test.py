from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from src.backend.use_case.watch.create_watch_highlight import CreateWatchHighlightUseCase


def test_create_watch_highlight_creates_highlight_and_context():
    """Проверяем, что CreateWatchHighlightUseCase создает хайлайт и сохраняет playback context."""
    create_highlight_use_case = Mock()
    create_highlight_use_case.execute.return_value = SimpleNamespace(id=33)
    watch_repo = Mock()
    use_case = CreateWatchHighlightUseCase(create_highlight_use_case, watch_repo)

    result = use_case.execute(
        user_id=1,
        anime_id=7,
        episode=2,
        title="best scene",
        start_timestamp=10.0,
        end_timestamp=20.0,
        description="great",
        is_spoiler=False,
        emotion="hype",
        watch_source_id=5,
        translation_id=6,
    )

    assert result.id == 33
    create_highlight_use_case.execute.assert_called_once()
    context = watch_repo.add_highlight_context.call_args.args[0]
    assert context.highlight_id == 33
    assert context.watch_source_id == 5
    assert context.translation_id == 6
    assert context.title == "best scene"
