"""DTO аутентификации: вход, регистрация, восстановление пароля."""

from backend.application.dto.auth.confirm_password_reset_command import ConfirmPasswordResetCommand
from backend.application.dto.auth.google_commands import (
    GoogleSignInCommand,
    LinkGoogleAccountCommand,
    UnlinkGoogleAccountCommand,
)
from backend.application.dto.auth.login_command import LoginCommand
from backend.application.dto.auth.logout_command import LogoutCommand
from backend.application.dto.auth.profile_overview_query import ProfileOverviewQuery
from backend.application.dto.auth.refresh_session_command import RefreshSessionCommand
from backend.application.dto.auth.register_command import RegisterCommand
from backend.application.dto.auth.request_password_reset_command import RequestPasswordResetCommand
from backend.application.dto.auth.resend_verification_command import ResendVerificationCommand
from backend.application.dto.auth.update_profile_command import UpdateProfileCommand
from backend.application.dto.auth.verify_email_command import VerifyEmailCommand

__all__ = [
    "ConfirmPasswordResetCommand",
    "GoogleSignInCommand",
    "LinkGoogleAccountCommand",
    "LoginCommand",
    "LogoutCommand",
    "ProfileOverviewQuery",
    "RefreshSessionCommand",
    "RegisterCommand",
    "RequestPasswordResetCommand",
    "ResendVerificationCommand",
    "UnlinkGoogleAccountCommand",
    "UpdateProfileCommand",
    "VerifyEmailCommand",
]
