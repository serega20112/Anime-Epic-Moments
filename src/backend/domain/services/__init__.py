"""Abstract service interfaces for the domain layer.

These interfaces declare the contracts that infrastructure adapters must
implement. The application layer depends on these abstractions, never on
concrete infrastructure classes.
"""

from backend.domain.services.anime_api_client import AnimeApiClientInterface
from backend.domain.services.email_verification_mailer import EmailVerificationMailerInterface
from backend.domain.services.email_verification_store import EmailVerificationStoreInterface
from backend.domain.services.highlight_dashboard_cache import HighlightDashboardCacheInterface
from backend.domain.services.jwt_service import JWTServiceInterface
from backend.domain.services.llm_client import LLMClientInterface
from backend.domain.services.password_reset_mailer import PasswordResetMailerInterface
from backend.domain.services.password_service import PasswordServiceInterface
from backend.domain.services.profile_overview_cache import ProfileOverviewCacheInterface
from backend.domain.services.recommendation_cache import RecommendationCacheInterface
from backend.domain.services.recommendation_service import RecommendationServiceInterface
from backend.domain.services.support_email_mailer import SupportEmailMailerInterface
from backend.domain.services.telegram_support_notifier import TelegramSupportNotifierInterface
from backend.domain.services.token_blocklist import TokenBlocklistInterface
from backend.domain.services.watch_source_provider import WatchSourceProviderInterface
from backend.domain.services.watch_source_sync_service import WatchSourceSyncServiceInterface

__all__ = [
    "AnimeApiClientInterface",
    "EmailVerificationMailerInterface",
    "EmailVerificationStoreInterface",
    "HighlightDashboardCacheInterface",
    "JWTServiceInterface",
    "LLMClientInterface",
    "PasswordResetMailerInterface",
    "PasswordServiceInterface",
    "ProfileOverviewCacheInterface",
    "RecommendationCacheInterface",
    "RecommendationServiceInterface",
    "SupportEmailMailerInterface",
    "TelegramSupportNotifierInterface",
    "TokenBlocklistInterface",
    "WatchSourceProviderInterface",
    "WatchSourceSyncServiceInterface",
]
