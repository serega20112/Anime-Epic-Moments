"""Use case for rotating auth tokens from a refresh token."""

from __future__ import annotations

import jwt

from backend.application.use_cases.auth.result import AuthResult
from backend.domain.services.jwt_service import JWTServiceInterface as JWTService
from backend.domain.services.token_blocklist import TokenBlocklistInterface


class RefreshSessionUseCase:
    """Validate a refresh token and return the owning user id.

    The use case rejects missing, revoked, or malformed refresh tokens and
    atomically consumes the old token so it cannot be reused even under
    concurrent requests, preparing a fresh pair of JWTs to be issued by the
    presentation layer.
    """

    def __init__(self, jwt_service: JWTService, token_blocklist: TokenBlocklistInterface):
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
        try:
            user_id = self.jwt_service.decode_refresh_token(token)
        except jwt.PyJWTError:
            return AuthResult.failure("invalid_token", "auth.refresh_session")
        ttl_seconds = self.jwt_service.get_token_ttl_seconds(token, expected_type="refresh")
        if not await self.token_blocklist.consume(token, ttl_seconds):
            return AuthResult.failure("invalid_token", "auth.refresh_session")
        return AuthResult.success(data=user_id)
