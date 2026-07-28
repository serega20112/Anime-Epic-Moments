import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from src.backend.dependencies.settings import Settings

logger = logging.getLogger("anime_epic_moments")


class CSRFService:
    """
    Service for CSRF protection using secure random tokens
    """
    
    def __init__(self):
        self.token_length = 32
        self.token_expire_minutes = 30
    
    def generate_token(self, request_state: Dict[str, Any]) -> str:
        """
        Generate and store CSRF token in request state
        
        Args:
            request_state: Request state dictionary for storing token
            
        Returns:
            CSRF token as string
        """
        token = secrets.token_urlsafe(self.token_length)
        request_state.csrf_token = {
            'value': token,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)).isoformat()
        }
        return token
    
    def get_token_from_state(self, request_state: Dict[str, Any]) -> Optional[str]:
        """
        Get CSRF token from request state
        
        Args:
            request_state: Request state dictionary
            
        Returns:
            CSRF token value or None
        """
        token_data = getattr(request_state, 'csrf_token', None)
        if token_data:
            return token_data['value']
        return None
    
    def validate_token(self, request_state: Dict[str, Any], token_from_request: str) -> bool:
        """
        Validate CSRF token from request against stored token
        
        Args:
            request_state: Request state with stored token
            token_from_request: Token from HTTP request
            
        Returns:
            True if valid, False otherwise
        """
        token_data = getattr(request_state, 'csrf_token', None)
        if not token_data:
            logger.warning("csrf_token_missing in request state")
            return False
        
        # Check if token exists and matches
        if token_data['value'] != token_from_request:
            logger.warning("csrf_token_mismatch")
            return False
        
        # Check expiration
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.utcnow() > expires_at:
            logger.warning("csrf_token_expired")
            delattr(request_state, 'csrf_token')  # Clean up expired token
            return False
        
        return True
    
    def validate_form_csrf(self, request_state: Dict[str, Any], form_data: Dict[str, Any]) -> bool:
        """
        Validate CSRF token from form data
        
        Args:
            request_state: Request state with stored token
            form_data: Form data containing CSRF token
            
        Returns:
            True if valid, False otherwise
        """
        form_token = form_data.get('csrf_token')
        if not form_token:
            logger.warning("csrf_token_missing_in_form")
            return False
        
        return self.validate_token(request_state, form_token)
    
    def validate_header_csrf(self, request_state: Dict[str, Any], authorization_header: str) -> bool:
        """
        Validate CSRF token from Authorization header
        
        Args:
            request_state: Request state with stored token
            authorization_header: Authorization header value
            
        Returns:
            True if valid, False otherwise
        """
        if not authorization_header or not authorization_header.startswith('Bearer '):
            logger.warning("csrf_invalid_header_format")
            return False
        
        token = authorization_header[7:]  # Remove 'Bearer ' prefix
        return self.validate_token(request_state, token)


# Global instance
csrf_service = CSRFService()