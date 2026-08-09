"""Use case for rotating auth tokens from a refresh token."""

from __future__ import annotations

from backend.application.use_cases.auth.result import AuthResult
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.token_blocklist import TokenBlocklist


class RefreshSessionUseCase:
    """Validate a refresh token and return the owning user id.

    The use case rejects missing, revoked, or malformed refresh tokens and
    blocks the old token so it cannot be reused, preparing a fresh pair of
    JWTs to be issued by the presentation layer.
    """

    def __init__(self, jwt_service: JWTService, token_blocklist: TokenBlocklist):
        """Initialize the use case.

        Args:
            jwt_service: JWT service.
            token_blocklist: Token blocklist.
        """
        self.jwt_service = jwt_service
        self.token_blocklist = token_blocklist

    async def execute(self, refresh_token: str) -> AuthResult:
        """Rotate a refresh token.

        Args:
            refresh_token: Current refresh token.

        Returns:
            AuthResult: Success with the user id or failure.
        """
        token = str(refresh_token or "").strip()
        if not token:
            return AuthResult.failure("auth_required", "auth.refresh_session")
        if await self.token_blocklist.is_revoked(token):
            return AuthResult.failure("invalid_token", "auth.refresh_session")
        try:
            user_id = self.jwt_service.decode_refresh_token(token)
        except Exception:
            return AuthResult.failure("invalid_token", "auth.refresh_session")
        await self.token_blocklist.revoke(
            token,
            self.jwt_service.get_token_ttl_seconds(token, expected_type="refresh"),
        )
        return AuthResult.success(data=user_id)
