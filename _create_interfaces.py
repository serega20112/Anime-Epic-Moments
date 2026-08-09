"""Create abstract service interfaces in src/domain/services/."""

import os

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.join(BASE, "src", "src/backend/domain", "services")
os.makedirs(SERVICES_DIR, exist_ok=True)

INTERFACES = {
    "password_service.py": '''"""Abstract password service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordServiceInterface(ABC):
    """Interface for password hashing and verification."""

    @abstractmethod
    def hash_password(self, plain_password: str) -> str:
        """Hash a plain password.

        Args:
            plain_password: The plain text password.

        Returns:
            str: The hashed password.
        """

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.

        Args:
            plain_password: The plain text password.
            hashed_password: The stored password hash.

        Returns:
            bool: True if the password matches the hash.
        """
''',
    "jwt_service.py": '''"""Abstract JWT service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class JWTServiceInterface(ABC):
    """Interface for JWT token creation and verification."""

    @abstractmethod
    def create_access_token(self, user_id: int) -> str:
        """Create an access token for a user.

        Args:
            user_id: The user identifier.

        Returns:
            str: The encoded JWT access token.
        """

    @abstractmethod
    def create_refresh_token(self, user_id: int) -> str:
        """Create a refresh token for a user.

        Args:
            user_id: The user identifier.

        Returns:
            str: The encoded JWT refresh token.
        """

    @abstractmethod
    def decode_token(self, token: str) -> int:
        """Decode an access token and return the user id.

        Args:
            token: The encoded JWT access token.

        Returns:
            int: The user identifier.

        Raises:
            Exception: If the token is invalid or expired.
        """

    @abstractmethod
    def decode_refresh_token(self, token: str) -> int:
        """Decode a refresh token and return the user id.

        Args:
            token: The encoded JWT refresh token.

        Returns:
            int: The user identifier.
        """

    @abstractmethod
    def create_password_reset_token(self, user_id: int, expires_minutes: int) -> str:
        """Create a password reset token.

        Args:
            user_id: The user identifier.
            expires_minutes: Token expiration in minutes.

        Returns:
            str: The encoded JWT password reset token.
        """

    @abstractmethod
    def decode_password_reset_token(self, token: str) -> int:
        """Decode a password reset token and return the user id.

        Args:
            token: The encoded JWT password reset token.

        Returns:
            int: The user identifier.
        """

    @abstractmethod
    def get_token_ttl_seconds(self, token: str, expected_type: str | None = None) -> int:
        """Get remaining TTL of a token in seconds.

        Args:
            token: The encoded JWT token.
            expected_type: Expected token type for validation.

        Returns:
            int: Remaining TTL in seconds.
        """
''',
    "anime_api_client.py": '''"""Abstract anime API client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AnimeApiClientInterface(ABC):
    """Interface for external anime data API clients."""

    @abstractmethod
    async def get_by_id(self, anime_id: int) -> Any:
        """Get anime data by id.

        Args:
            anime_id: The anime identifier.

        Returns:
            Any: Anime data object or None.
        """

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[Any]:
        """Search anime by text query.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            list[Any]: List of anime data objects.
        """

    @abstractmethod
    async def autocomplete(self, prefix: str, limit: int = 8) -> list[Any]:
        """Autocomplete anime titles by prefix.

        Args:
            prefix: Title prefix to search.
            limit: Maximum number of results.

        Returns:
            list[Any]: List of anime data objects.
        """

    @abstractmethod
    async def get_season_popular(self, limit: int = 12) -> list[Any]:
        """Get popular anime for the current season.

        Args:
            limit: Maximum number of results.

        Returns:
            list[Any]: List of anime data objects.
        """
''',
    "llm_client.py": '''"""Abstract LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMClientInterface(ABC):
    """Interface for LLM-based AI clients."""

    @abstractmethod
    async def describe_taste_profile(self, profile_data: dict, fallback: str) -> str:
        """Generate a taste profile description.

        Args:
            profile_data: Dictionary of profile attributes.
            fallback: Fallback text if AI is unavailable.

        Returns:
            str: Generated or fallback description.
        """

    @abstractmethod
    async def search_by_description(self, description: str, limit: int = 5) -> list[Any]:
        """Search anime by natural language description.

        Args:
            description: Natural language anime description.
            limit: Maximum number of results.

        Returns:
            list[Any]: List of anime data objects.
        """
''',
    "profile_overview_cache.py": '''"""Abstract profile overview cache interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProfileOverviewCacheInterface(ABC):
    """Interface for caching user profile overviews."""

    @abstractmethod
    async def get_overview(self, user_id: int) -> Any:
        """Get cached profile overview.

        Args:
            user_id: The user identifier.

        Returns:
            Any: Cached ProfileOverview or None.
        """

    @abstractmethod
    async def set_overview(self, user_id: int, overview: Any) -> Any:
        """Store profile overview in cache.

        Args:
            user_id: The user identifier.
            overview: ProfileOverview to cache.

        Returns:
            Any: The stored overview.
        """

    @abstractmethod
    async def get_ai_summary(self, user_id: int) -> str | None:
        """Get cached AI taste summary.

        Args:
            user_id: The user identifier.

        Returns:
            str | None: Cached summary or None.
        """

    @abstractmethod
    async def set_ai_summary(self, user_id: int, summary: str) -> None:
        """Store AI taste summary in cache.

        Args:
            user_id: The user identifier.
            summary: Summary text to cache.
        """

    @abstractmethod
    async def invalidate(self, user_id: int) -> None:
        """Invalidate cached data for a user.

        Args:
            user_id: The user identifier.
        """
''',
    "highlight_dashboard_cache.py": '''"""Abstract highlight dashboard cache interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class HighlightDashboardCacheInterface(ABC):
    """Interface for caching highlight dashboard data."""

    @abstractmethod
    async def get_dashboard(self, key: str) -> Any:
        """Get cached dashboard data.

        Args:
            key: Cache key.

        Returns:
            Any: Cached dashboard data or None.
        """

    @abstractmethod
    async def set_dashboard(self, key: str, data: Any, ttl_seconds: int | None = None) -> None:
        """Store dashboard data in cache.

        Args:
            key: Cache key.
            data: Dashboard data to cache.
            ttl_seconds: Optional TTL in seconds.
        """

    @abstractmethod
    async def invalidate(self, key: str | None = None) -> None:
        """Invalidate cached dashboard data.

        Args:
            key: Optional specific key to invalidate. If None, invalidates all.
        """
''',
    "email_verification_store.py": '''"""Abstract email verification store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmailVerificationStoreInterface(ABC):
    """Interface for storing email verification codes."""

    @abstractmethod
    async def generate_code(self, email: str, password: str, username: str, theme: str) -> str:
        """Generate and store a verification code.

        Args:
            email: User email.
            password: User password.
            username: User username.
            theme: User theme preference.

        Returns:
            str: Generated verification code.
        """

    @abstractmethod
    async def verify_code(self, email: str, code: str) -> dict | None:
        """Verify a code and return stored registration data.

        Args:
            email: User email.
            code: Verification code.

        Returns:
            dict | None: Registration data if valid, None otherwise.
        """

    @abstractmethod
    async def has_pending(self, email: str) -> bool:
        """Check if a pending verification exists.

        Args:
            email: User email.

        Returns:
            bool: True if pending verification exists.
        """
''',
    "email_verification_mailer.py": '''"""Abstract email verification mailer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmailVerificationMailerInterface(ABC):
    """Interface for sending email verification messages."""

    @abstractmethod
    async def send_verification_email(self, email: str, code: str) -> None:
        """Send a verification email with a code.

        Args:
            email: Recipient email.
            code: Verification code.
        """
''',
    "password_reset_mailer.py": '''"""Abstract password reset mailer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordResetMailerInterface(ABC):
    """Interface for sending password reset emails."""

    @abstractmethod
    async def send_reset_email(self, email: str, reset_url: str) -> None:
        """Send a password reset email.

        Args:
            email: Recipient email.
            reset_url: Password reset URL.
        """
''',
    "support_email_mailer.py": '''"""Abstract support email mailer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SupportEmailMailerInterface(ABC):
    """Interface for sending support ticket emails."""

    @abstractmethod
    async def send(self, ticket_data: dict[str, Any]) -> None:
        """Send a support ticket email.

        Args:
            ticket_data: Dictionary with ticket information.
        """
''',
    "telegram_support_notifier.py": '''"""Abstract Telegram support notifier interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TelegramSupportNotifierInterface(ABC):
    """Interface for sending Telegram support notifications."""

    @abstractmethod
    async def notify(self, ticket_data: dict[str, Any]) -> None:
        """Send a Telegram notification about a support ticket.

        Args:
            ticket_data: Dictionary with ticket information.
        """
''',
    "watch_source_sync_service.py": '''"""Abstract watch source sync service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WatchSourceSyncServiceInterface(ABC):
    """Interface for syncing watch sources."""

    @abstractmethod
    async def sync_sources(self, anime_id: int) -> list[Any]:
        """Sync watch sources for an anime.

        Args:
            anime_id: The anime identifier.

        Returns:
            list[Any]: List of watch source objects.
        """

    @abstractmethod
    async def add_watch_source(self, source_data: dict[str, Any]) -> Any:
        """Add a watch source.

        Args:
            source_data: Dictionary with source information.

        Returns:
            Any: The created watch source.
        """
''',
    "recommendation_service.py": '''"""Abstract recommendation service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RecommendationServiceInterface(ABC):
    """Interface for generating anime recommendations."""

    @abstractmethod
    async def generate_recommendations(self, user_id: int) -> list[Any]:
        """Generate recommendations for a user.

        Args:
            user_id: The user identifier.

        Returns:
            list[Any]: List of recommendation objects.
        """

    @abstractmethod
    async def refresh_recommendations(self, user_id: int) -> list[Any]:
        """Refresh recommendations for a user.

        Args:
            user_id: The user identifier.

        Returns:
            list[Any]: List of refreshed recommendation objects.
        """
''',
}


def main() -> None:
    """Create all interface files."""
    for name, content in INTERFACES.items():
        path = os.path.join(SERVICES_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {os.path.relpath(path, BASE)}")
    print(f"\nCreated {len(INTERFACES)} interface files")


if __name__ == "__main__":
    main()
