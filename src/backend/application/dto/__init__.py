"""Data transfer objects for application layer commands and queries."""

from backend.application.dto.anime_queries import (
    AutocompleteAnimeQuery,
    GetSeasonPopularQuery,
    SearchAnimeByDescriptionQuery,
    SearchAnimeQuery,
)
from backend.application.dto.auth_commands import (
    ConfirmPasswordResetCommand,
    LoginCommand,
    RegisterCommand,
    RequestPasswordResetCommand,
    ResendVerificationCommand,
    UpdateProfileCommand,
    VerifyEmailCommand,
)
from backend.application.dto.collection_commands import (
    AddCollectionItemCommand,
    CreateCollectionCommand,
    RemoveCollectionItemCommand,
)
from backend.application.dto.highlight_commands import (
    AddHighlightCommentCommand,
    CreateHighlightCommand,
    DeleteHighlightCommand,
    EditHighlightCommand,
    HighlightDashboardQuery,
    HighlightFeedQuery,
    HighlightListQuery,
    SetHighlightLikeCommand,
    SetSavedHighlightCommand,
)
from backend.application.dto.recommendation_commands import AskAiRecommendationsCommand
from backend.application.dto.support_commands import CreateSupportTicketCommand
from backend.application.dto.watch_commands import (
    AddAnimeCommentCommand,
    CreateWatchHighlightCommand,
    SaveViewingSessionCommand,
    SetAnimeCommentLikeCommand,
    UpsertUserAnimeStatusCommand,
    WatchPageQuery,
)

__all__ = [
    "AddAnimeCommentCommand",
    "AddCollectionItemCommand",
    "AddHighlightCommentCommand",
    "AskAiRecommendationsCommand",
    "AutocompleteAnimeQuery",
    "ConfirmPasswordResetCommand",
    "CreateCollectionCommand",
    "CreateHighlightCommand",
    "CreateSupportTicketCommand",
    "CreateWatchHighlightCommand",
    "DeleteHighlightCommand",
    "EditHighlightCommand",
    "GetSeasonPopularQuery",
    "HighlightDashboardQuery",
    "HighlightFeedQuery",
    "HighlightListQuery",
    "LoginCommand",
    "RegisterCommand",
    "RemoveCollectionItemCommand",
    "RequestPasswordResetCommand",
    "ResendVerificationCommand",
    "SaveViewingSessionCommand",
    "SearchAnimeByDescriptionQuery",
    "SearchAnimeQuery",
    "SetAnimeCommentLikeCommand",
    "SetHighlightLikeCommand",
    "SetSavedHighlightCommand",
    "UpdateProfileCommand",
    "UpsertUserAnimeStatusCommand",
    "VerifyEmailCommand",
    "WatchPageQuery",
]
