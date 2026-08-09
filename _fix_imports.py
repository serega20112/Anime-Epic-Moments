"""Replace infrastructure imports in application layer with domain interface imports."""

import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

REPLACEMENTS = [
    (
        "from src.infrastructure.security.password_service import PasswordService",
        "from src.domain.services.password_service import PasswordServiceInterface as PasswordService",
    ),
    (
        "from src.infrastructure.security.jwt_service import JWTService",
        "from src.domain.services.jwt_service import JWTServiceInterface as JWTService",
    ),
    (
        "from src.infrastructure.external.anime_api_client import AnimeApiClient",
        "from src.domain.services.anime_api_client import AnimeApiClientInterface as AnimeApiClient",
    ),
    (
        "from src.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient",
        "from src.domain.services.llm_client import LLMClientInterface as HuggingFaceLLMClient",
    ),
    (
        "from src.infrastructure.cache.profile_overview_cache import ProfileOverviewCache",
        "from src.domain.services.profile_overview_cache import ProfileOverviewCacheInterface as ProfileOverviewCache",
    ),
    (
        "from src.infrastructure.cache.highlight_dashboard_cache import (\n    HighlightDashboardCache,\n)",
        "from src.domain.services.highlight_dashboard_cache import HighlightDashboardCacheInterface as HighlightDashboardCache",
    ),
    (
        "from src.infrastructure.cache.highlight_dashboard_cache import (\n    HighlightDashboardCache,\n    invalidate_highlight_dashboard_cache,\n)",
        "from src.domain.services.highlight_dashboard_cache import HighlightDashboardCacheInterface as HighlightDashboardCache",
    ),
    (
        "from src.infrastructure.security.email_verification_store import (\n    EmailVerificationStore,\n)",
        "from src.domain.services.email_verification_store import EmailVerificationStoreInterface as EmailVerificationStore",
    ),
    (
        "from src.infrastructure.security.email_verification_store import EmailVerificationStore",
        "from src.domain.services.email_verification_store import EmailVerificationStoreInterface as EmailVerificationStore",
    ),
    (
        "from src.infrastructure.external.email_verification_mailer import (\n    EmailVerificationMailer,\n)",
        "from src.domain.services.email_verification_mailer import EmailVerificationMailerInterface as EmailVerificationMailer",
    ),
    (
        "from src.infrastructure.external.email_verification_mailer import EmailVerificationMailer",
        "from src.domain.services.email_verification_mailer import EmailVerificationMailerInterface as EmailVerificationMailer",
    ),
    (
        "from src.infrastructure.external.password_reset_mailer import (\n    PasswordResetMailer,\n)",
        "from src.domain.services.password_reset_mailer import PasswordResetMailerInterface as PasswordResetMailer",
    ),
    (
        "from src.infrastructure.external.password_reset_mailer import PasswordResetMailer",
        "from src.domain.services.password_reset_mailer import PasswordResetMailerInterface as PasswordResetMailer",
    ),
    (
        "from src.infrastructure.external.support_email_mailer import SupportEmailMailer",
        "from src.domain.services.support_email_mailer import SupportEmailMailerInterface as SupportEmailMailer",
    ),
    (
        "from src.infrastructure.external.telegram_support_notifier import (\n    TelegramSupportNotifier,\n)",
        "from src.domain.services.telegram_support_notifier import TelegramSupportNotifierInterface as TelegramSupportNotifier",
    ),
    (
        "from src.infrastructure.external.telegram_support_notifier import TelegramSupportNotifier",
        "from src.domain.services.telegram_support_notifier import TelegramSupportNotifierInterface as TelegramSupportNotifier",
    ),
    (
        "from src.infrastructure.repositories.user_repository import UserRepository",
        "from src.domain.repositories.user_repository import UserRepository",
    ),
    (
        "from src.infrastructure.repositories.collection_repository import (\n    CollectionRepository,\n)",
        "from src.domain.repositories.collection_repository import CollectionRepository",
    ),
    (
        "from src.infrastructure.repositories.collection_repository import CollectionRepository",
        "from src.domain.repositories.collection_repository import CollectionRepository",
    ),
    (
        "from src.application.services.recommendation_service import RecommendationService",
        "from src.domain.services.recommendation_service import RecommendationServiceInterface as RecommendationService",
    ),
    (
        "from src.application.services.watch_source_sync_service import WatchSourceSyncService",
        "from src.domain.services.watch_source_sync_service import WatchSourceSyncServiceInterface as WatchSourceSyncService",
    ),
]


def fix_file(file_path: str) -> bool:
    """Replace infrastructure imports in a single file. Returns True if changed."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False

    original = content
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)

    content = re.sub(
        r"from src\.infrastructure\.cache\.highlight_dashboard_cache import \(\s*HighlightDashboardCache,\s*\)",
        "from src.domain.services.highlight_dashboard_cache import HighlightDashboardCacheInterface as HighlightDashboardCache",
        content,
    )
    content = re.sub(
        r"from src\.infrastructure\.security\.email_verification_store import \(\s*EmailVerificationStore,\s*\)",
        "from src.domain.services.email_verification_store import EmailVerificationStoreInterface as EmailVerificationStore",
        content,
    )
    content = re.sub(
        r"from src\.infrastructure\.external\.email_verification_mailer import \(\s*EmailVerificationMailer,\s*\)",
        "from src.domain.services.email_verification_mailer import EmailVerificationMailerInterface as EmailVerificationMailer",
        content,
    )
    content = re.sub(
        r"from src\.infrastructure\.external\.password_reset_mailer import \(\s*PasswordResetMailer,\s*\)",
        "from src.domain.services.password_reset_mailer import PasswordResetMailerInterface as PasswordResetMailer",
        content,
    )
    content = re.sub(
        r"from src\.infrastructure\.external\.telegram_support_notifier import \(\s*TelegramSupportNotifier,\s*\)",
        "from src.domain.services.telegram_support_notifier import TelegramSupportNotifierInterface as TelegramSupportNotifier",
        content,
    )

    if content != original:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main() -> None:
    """Fix imports in all application layer files."""
    app_dir = os.path.join(BASE, "src", "src/backend/application")
    changed = 0
    for dirpath, _dirnames, filenames in os.walk(app_dir):
        if "__pycache__" in dirpath:
            continue
        for filename in filenames:
            if not filename.endswith(".py") or filename == "__init__.py":
                continue
            file_path = os.path.join(dirpath, filename)
            if fix_file(file_path):
                changed += 1
                print(f"Fixed: {os.path.relpath(file_path, BASE)}")
    print(f"\nFixed imports in {changed} files")


if __name__ == "__main__":
    main()
