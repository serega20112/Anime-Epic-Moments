"""Use case for logging out a user by revoking their auth tokens."""

from __future__ import annotations

import logging

from backend.application.interface.services.jwt_service import JWTServiceInterface as JWTService
from backend.application.interface.services.token_blocklist import TokenBlocklistInterface
from backend.application.use_cases.auth.result import AuthResult

logger = logging.getLogger("anime_epic_moments")


class LogoutUserUseCase:
    """Invalidate access and refresh tokens so they can no longer be used."""

    def __init__(self, jwt_service: JWTService, token_blocklist: TokenBlocklistInterface):
        """Initialize the use case.

        Args:
            jwt_service: JWT service.
            token_blocklist: Token blocklist.
        """
        self.jwt_service = jwt_service
        self.token_blocklist = token_blocklist

    async def execute(self, access_token: str, refresh_token: str) -> AuthResult:
        """Revoke the provided auth tokens.

        Args:
            access_token: Current access token (may be empty).
            refresh_token: Current refresh token (may be empty).

        Returns:
            AuthResult: Success toward the index page.
        """
        tokens = (
            (str(access_token or "").strip(), "access"),
            (str(refresh_token or "").strip(), "refresh"),
        )
        for token, expected_type in tokens:
            if not token:
                continue
            try:
                await self.token_blocklist.revoke(
                    token,
                    await self.jwt_service.get_token_ttl_seconds(
                        token, expected_type=expected_type
                    ),
                )
            except Exception:
                logger.warning("token_revoke_failed type=%s", expected_type, exc_info=True)
        return await AuthResult.success(redirect_endpoint="index.index")
