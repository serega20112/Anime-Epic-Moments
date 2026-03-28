from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.watch.upsert_user_anime_status import UpsertUserAnimeStatusUseCase


def test_upsert_user_anime_status_persists_domain_object():
    """Проверяем, что UpsertUserAnimeStatusUseCase передает в репозиторий корректный UserAnimeStatus."""
    watch_repo = Mock()
    watch_repo.upsert_status.return_value = "saved"
    use_case = UpsertUserAnimeStatusUseCase(watch_repo)

    result = use_case.execute(user_id=1, anime_id=9, status="watching")

    assert result == "saved"
    status = watch_repo.upsert_status.call_args.args[0]
    assert status.user_id == 1
    assert status.anime_id == 9
    assert status.status == "watching"
