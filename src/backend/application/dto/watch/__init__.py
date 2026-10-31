"""DTO просмотра: сессии, прогресс, обсуждение, источники."""

from backend.application.dto.watch.add_anime_comment_command import AddAnimeCommentCommand
from backend.application.dto.watch.add_watch_source_command import AddWatchSourceCommand
from backend.application.dto.watch.anime_discussion_query import AnimeDiscussionQuery
from backend.application.dto.watch.complete_episode_command import CompleteEpisodeCommand
from backend.application.dto.watch.create_watch_highlight_command import CreateWatchHighlightCommand
from backend.application.dto.watch.save_viewing_session_command import SaveViewingSessionCommand
from backend.application.dto.watch.set_anime_comment_like_command import SetAnimeCommentLikeCommand
from backend.application.dto.watch.sync_watch_sources_query import SyncWatchSourcesQuery
from backend.application.dto.watch.upsert_user_anime_status_command import (
    UpsertUserAnimeStatusCommand,
)
from backend.application.dto.watch.watch_page_query import WatchPageQuery

__all__ = [
    "AddAnimeCommentCommand",
    "AddWatchSourceCommand",
    "AnimeDiscussionQuery",
    "CompleteEpisodeCommand",
    "CreateWatchHighlightCommand",
    "SaveViewingSessionCommand",
    "SetAnimeCommentLikeCommand",
    "SyncWatchSourcesQuery",
    "UpsertUserAnimeStatusCommand",
    "WatchPageQuery",
]
