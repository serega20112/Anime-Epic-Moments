"""Data transfer objects for application layer commands and queries."""

from backend.application.dto.anime import (
    AutocompleteAnimeQuery,
    FilterAnimeCatalogQuery,
    GetSeasonPopularQuery,
    SearchAnimeByDescriptionQuery,
    SearchAnimeQuery,
)
from backend.application.dto.auth import (
    ConfirmPasswordResetCommand,
    LoginCommand,
    RegisterCommand,
    RequestPasswordResetCommand,
    ResendVerificationCommand,
    UpdateProfileCommand,
    VerifyEmailCommand,
)
from backend.application.dto.collection import (
    AddCollectionItemCommand,
    CreateCollectionCommand,
    RemoveCollectionItemCommand,
)
from backend.application.dto.highlight import (
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
from backend.application.dto.moment import (
    PublishViewingMomentCommand,
    SaveViewingMomentCommand,
)
from backend.application.dto.reaction import (
    GetEpisodeReactionsQuery,
    SetEpisodeReactionCommand,
)
from backend.application.dto.recommendation import AskAiRecommendationsCommand
from backend.application.dto.support import CreateSupportTicketCommand
from backend.application.dto.watch import (
    AddAnimeCommentCommand,
    CompleteEpisodeCommand,
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
    "CompleteEpisodeCommand",
    "CreateCollectionCommand",
    "CreateHighlightCommand",
    "CreateSupportTicketCommand",
    "CreateWatchHighlightCommand",
    "DeleteHighlightCommand",
    "EditHighlightCommand",
    "FilterAnimeCatalogQuery",
    "GetEpisodeReactionsQuery",
    "GetSeasonPopularQuery",
    "HighlightDashboardQuery",
    "HighlightFeedQuery",
    "HighlightListQuery",
    "LoginCommand",
    "PublishViewingMomentCommand",
    "RegisterCommand",
    "RemoveCollectionItemCommand",
    "RequestPasswordResetCommand",
    "ResendVerificationCommand",
    "SaveViewingSessionCommand",
    "SaveViewingMomentCommand",
    "SearchAnimeByDescriptionQuery",
    "SearchAnimeQuery",
    "SetAnimeCommentLikeCommand",
    "SetEpisodeReactionCommand",
    "SetHighlightLikeCommand",
    "SetSavedHighlightCommand",
    "UpdateProfileCommand",
    "UpsertUserAnimeStatusCommand",
    "VerifyEmailCommand",
    "WatchPageQuery",
]
