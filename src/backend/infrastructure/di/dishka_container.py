"""Dishka container setup for the application."""

from __future__ import annotations

from dishka import AsyncContainer, make_async_container

from backend.infrastructure.di.providers import (
    AnimeUseCaseProvider,
    AppProvider,
    AuthUseCaseProvider,
    CollectionUseCaseProvider,
    FavoriteUseCaseProvider,
    HighlightUseCaseProvider,
    MomentUseCaseProvider,
    RatingUseCaseProvider,
    ReactionUseCaseProvider,
    RequestProvider,
    SupportUseCaseProvider,
    UserUseCaseProvider,
    WatchUseCaseProvider,
)


def build_dishka_container() -> AsyncContainer:
    """Build the application Dishka container.

    Returns:
        AsyncContainer: Configured Dishka container.
    """
    return make_async_container(
        AppProvider(),
        RequestProvider(),
        AuthUseCaseProvider(),
        HighlightUseCaseProvider(),
        FavoriteUseCaseProvider(),
        CollectionUseCaseProvider(),
        WatchUseCaseProvider(),
        ReactionUseCaseProvider(),
        RatingUseCaseProvider(),
        MomentUseCaseProvider(),
        AnimeUseCaseProvider(),
        UserUseCaseProvider(),
        SupportUseCaseProvider(),
    )
