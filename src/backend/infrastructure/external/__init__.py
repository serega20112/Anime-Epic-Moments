"""Facade re-exports for backend.infrastructure.external."""

from __future__ import annotations

from backend.infrastructure.external.aniboom_provider import AniBoomProvider
from backend.infrastructure.external.anilibria_client import AniLibriaClient
from backend.infrastructure.external.anime_api_client import AnimeApiClient
from backend.infrastructure.external.animego_provider import AnimeGoProvider
from backend.infrastructure.external.eporner_provider import EpornerProvider
from backend.infrastructure.external.hanime_provider import HanimeProvider
from backend.infrastructure.external.hdrezka_provider import HDRezkaProvider
from backend.infrastructure.external.justwatch_client import JustWatchClient
from backend.infrastructure.external.kinobox_provider import KinoboxProvider
from backend.infrastructure.external.kodik_client import KodikClient
from backend.infrastructure.external.password_reset_mailer import PasswordResetMailer
from backend.infrastructure.external.sameband_provider import SamebandProvider
from backend.infrastructure.external.shikimori_client import ShikimoriClient
from backend.infrastructure.external.sibnet_provider import SibnetProvider
from backend.infrastructure.external.support_email_mailer import SupportEmailMailer
from backend.infrastructure.external.telegram_support_notifier import TelegramSupportNotifier
from backend.infrastructure.external.watch_source_provider import WatchSourceProvider

__all__ = [
    "AniLibriaClient",
    "AniBoomProvider",
    "AnimeApiClient",
    "AnimeGoProvider",
    "EpornerProvider",
    "HDRezkaProvider",
    "HanimeProvider",
    "JustWatchClient",
    "KinoboxProvider",
    "KodikClient",
    "PasswordResetMailer",
    "SamebandProvider",
    "SibnetProvider",
    "ShikimoriClient",
    "SupportEmailMailer",
    "TelegramSupportNotifier",
    "WatchSourceProvider",
]
