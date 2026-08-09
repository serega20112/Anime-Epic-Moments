"""Dishka container setup for the application."""

from __future__ import annotations

from dishka import AsyncContainer, make_async_container

from backend.infrastructure.di.providers import AppProvider, RequestProvider, UseCaseProvider


def build_dishka_container() -> AsyncContainer:
    """Build the application Dishka container.

    Returns:
        AsyncContainer: Configured Dishka container.
    """
    return make_async_container(
        AppProvider(),
        RequestProvider(),
        UseCaseProvider(),
    )
