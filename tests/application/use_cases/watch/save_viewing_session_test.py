from __future__ import annotations

from unittest.mock import Mock

from backend.application.use_cases.watch.save_viewing_session import SaveViewingSessionUseCase


def test_save_viewing_session_persists_session_object():
    """Проверяем, что SaveViewingSessionUseCase передает в репозиторий корректную ViewingSession."""
    watch_repo = Mock()
    profile_cache = Mock()
    watch_repo.upsert_session.return_value = "saved"
    use_case = SaveViewingSessionUseCase(watch_repo, profile_cache)

    result = use_case.execute(
        user_id=1,
        anime_id=7,
        episode=2,
        watch_source_id=3,
        position_seconds=15.5,
        volume=0.4,
        quality_label="1080",
        is_paused=False,
    )

    assert result == "saved"
    session = watch_repo.upsert_session.call_args.args[0]
    assert session.user_id == 1
    assert session.watch_source_id == 3
    assert session.position_seconds == 15.5
    profile_cache.invalidate_overview.assert_called_once_with(1)
