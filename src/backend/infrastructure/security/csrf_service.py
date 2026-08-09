"""CSRF protection service using secure random tokens with expiration."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("anime_epic_moments")


class CSRFService:
    """Generates and validates CSRF tokens stored in request state."""

    def __init__(self) -> None:
        self.token_length: int = 32
        self.token_expire_minutes: int = 30

    def generate_token(self, request_state: Any) -> str:
        """Generate a secure random CSRF token and store it in request state.

        Args:
            request_state: Request state object to store the token.

        Returns:
            str: Generated CSRF token value.
        """
        token = secrets.token_urlsafe(self.token_length)
        request_state.csrf_token = {
            "value": token,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (
                datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
            ).isoformat(),
        }
        return token

    def get_token_from_state(self, request_state: Any) -> str | None:
        """Retrieve the CSRF token value from request state.

        Args:
            request_state: Request state containing the token.

        Returns:
            str | None: Token value or None if not present.
        """
        token_data = getattr(request_state, "csrf_token", None)
        if token_data:
            return token_data["value"]
        return None

    def validate_token(self, request_state: Any, token_from_request: str) -> bool:
        """Validate a CSRF token against the stored token in request state.

        Checks token existence, value match, and expiration.

        Args:
            request_state: Request state with stored token.
            token_from_request: Token submitted with the request.

        Returns:
            bool: True if the token is valid and not expired.
        """
        token_data = getattr(request_state, "csrf_token", None)
        if not token_data:
            logger.warning("csrf_token_missing in request state")
            return False

        if token_data["value"] != token_from_request:
            logger.warning("csrf_token_mismatch")
            return False

        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.utcnow() > expires_at:
            logger.warning("csrf_token_expired")
            delattr(request_state, "csrf_token")
            return False

        return True

    def validate_form_csrf(self, request_state: Any, form_data: dict[str, Any]) -> bool:
        """Validate CSRF token from form data.

        Args:
            request_state: Request state with stored token.
            form_data: Form data containing csrf_token field.

        Returns:
            bool: True if token is valid.
        """
        form_token = form_data.get("csrf_token")
        if not form_token:
            logger.warning("csrf_token_missing_in_form")
            return False

        return self.validate_token(request_state, form_token)

    def validate_header_csrf(self, request_state: Any, authorization_header: str) -> bool:
        """Validate CSRF token from Authorization header.

        Expects header in format "Bearer <token>".

        Args:
            request_state: Request state with stored token.
            authorization_header: Value of Authorization header.

        Returns:
            bool: True if token is valid.
        """
        if not authorization_header or not authorization_header.startswith("Bearer "):
            logger.warning("csrf_invalid_header_format")
            return False

        token = authorization_header[7:]
        return self.validate_token(request_state, token)


csrf_service = CSRFService()
