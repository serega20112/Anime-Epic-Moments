"""Facade re-exports for backend.infrastructure.external."""

from __future__ import annotations

from backend.infrastructure.external.anilibria_client import AniLibriaClient
from backend.infrastructure.external.anime_api_client import AnimeApiClient
from backend.infrastructure.external.justwatch_client import JustWatchClient
from backend.infrastructure.external.kodik_client import KodikClient
from backend.infrastructure.external.password_reset_mailer import PasswordResetMailer
from backend.infrastructure.external.support_email_mailer import SupportEmailMailer
from backend.infrastructure.external.telegram_support_notifier import TelegramSupportNotifier
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

__all__ = [
    "AniLibriaClient",
    "AnimeApiClient",
    "JustWatchClient",
    "KodikClient",
    "PasswordResetMailer",
    "SupportEmailMailer",
    "TelegramSupportNotifier",
    "WatchSourceProvider",
]
