"""Auth use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.use_cases import (
    LogoutUserUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
    RequestEmailVerificationUseCase,
    RequestPasswordResetUseCase,
    ResendEmailVerificationUseCase,
    UpdateUserProfileUseCase,
    VerifyEmailUseCase,
)
from backend.application.use_cases.auth.login_user import LoginUserUseCase
from backend.application.use_cases.auth.reset_password import ResetPasswordUseCase
from backend.domain.unit_of_work import UnitOfWorkInterface
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import PasswordResetMailer
from backend.infrastructure.external.email_verification_mailer import EmailVerificationMailer
from backend.infrastructure.repositories.user_repository import UserRepository
from backend.infrastructure.security.account_lock_service import AccountLockService
from backend.infrastructure.security.email_verification_store import EmailVerificationStore
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.password_service import PasswordService
from backend.infrastructure.security.token_blocklist import TokenBlocklist


class AuthUseCaseProvider(Provider):
    """Provide authentication and account use cases."""

    @provide(scope=Scope.REQUEST)
    def register_user(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        unit_of_work: UnitOfWorkInterface,
    ) -> RegisterUserUseCase:
        """Provide the register user use case.

        Args:
            user_repository: User repository.
            password_service: Password service.
            unit_of_work: Transaction boundary.

        Returns:
            RegisterUserUseCase: Configured use case.
        """
        return RegisterUserUseCase(user_repository, password_service, unit_of_work)

    @provide(scope=Scope.REQUEST)
    def request_email_verification(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        email_verification_store: EmailVerificationStore,
        email_verification_mailer: EmailVerificationMailer,
    ) -> RequestEmailVerificationUseCase:
        """Provide the request email verification use case.

        Args:
            user_repository: User repository.
            password_service: Password service.
            email_verification_store: Verification store.
            email_verification_mailer: Verification mailer.

        Returns:
            RequestEmailVerificationUseCase: Configured use case.
        """
        return RequestEmailVerificationUseCase(
            user_repository,
            password_service,
            email_verification_store,
            email_verification_mailer,
        )

    @provide(scope=Scope.REQUEST)
    def resend_email_verification(
        self,
        email_verification_store: EmailVerificationStore,
        email_verification_mailer: EmailVerificationMailer,
    ) -> ResendEmailVerificationUseCase:
        """Provide the resend email verification use case.

        Args:
            email_verification_store: Verification store.
            email_verification_mailer: Verification mailer.

        Returns:
            ResendEmailVerificationUseCase: Configured use case.
        """
        return ResendEmailVerificationUseCase(
            email_verification_store,
            email_verification_mailer,
        )

    @provide(scope=Scope.REQUEST)
    def verify_email(
        self,
        user_repository: UserRepository,
        email_verification_store: EmailVerificationStore,
        unit_of_work: UnitOfWorkInterface,
    ) -> VerifyEmailUseCase:
        """Provide the verify email use case.

        Args:
            user_repository: User repository.
            email_verification_store: Verification store.
            unit_of_work: Transaction boundary.

        Returns:
            VerifyEmailUseCase: Configured use case.
        """
        return VerifyEmailUseCase(user_repository, email_verification_store, unit_of_work)

    @provide(scope=Scope.REQUEST)
    def login_user(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        account_lock_service: AccountLockService,
    ) -> LoginUserUseCase:
        """Provide the login user use case.

        Args:
            user_repository: User repository.
            password_service: Password service.
            account_lock_service: Account lockout service.

        Returns:
            LoginUserUseCase: Configured use case.
        """
        return LoginUserUseCase(user_repository, password_service, account_lock_service)

    @provide(scope=Scope.REQUEST)
    def logout_user(
        self,
        jwt_service: JWTService,
        token_blocklist: TokenBlocklist,
    ) -> LogoutUserUseCase:
        """Provide the logout user use case.

        Args:
            jwt_service: JWT service.
            token_blocklist: Token blocklist.

        Returns:
            LogoutUserUseCase: Configured use case.
        """
        return LogoutUserUseCase(jwt_service, token_blocklist)

    @provide(scope=Scope.REQUEST)
    def refresh_session(
        self,
        jwt_service: JWTService,
        token_blocklist: TokenBlocklist,
    ) -> RefreshSessionUseCase:
        """Provide the refresh session use case.

        Args:
            jwt_service: JWT service.
            token_blocklist: Token blocklist.

        Returns:
            RefreshSessionUseCase: Configured use case.
        """
        return RefreshSessionUseCase(jwt_service, token_blocklist)

    @provide(scope=Scope.REQUEST)
    def update_user_profile(
        self,
        user_repository: UserRepository,
        profile_overview_cache: ProfileOverviewCache,
        unit_of_work: UnitOfWorkInterface,
    ) -> UpdateUserProfileUseCase:
        """Provide the update user profile use case.

        Args:
            user_repository: User repository.
            profile_overview_cache: Profile overview cache.
            unit_of_work: Transaction boundary.

        Returns:
            UpdateUserProfileUseCase: Configured use case.
        """
        return UpdateUserProfileUseCase(user_repository, profile_overview_cache, unit_of_work)

    @provide(scope=Scope.REQUEST)
    def request_password_reset(
        self,
        user_repository: UserRepository,
        jwt_service: JWTService,
        password_reset_mailer: PasswordResetMailer,
    ) -> RequestPasswordResetUseCase:
        """Provide the request password reset use case.

        Args:
            user_repository: User repository.
            jwt_service: JWT service.
            password_reset_mailer: Password reset mailer.

        Returns:
            RequestPasswordResetUseCase: Configured use case.
        """
        return RequestPasswordResetUseCase(
            user_repository,
            jwt_service,
            password_reset_mailer,
        )

    @provide(scope=Scope.REQUEST)
    def reset_password(
        self,
        user_repository: UserRepository,
        jwt_service: JWTService,
        password_service: PasswordService,
        token_blocklist: TokenBlocklist,
        unit_of_work: UnitOfWorkInterface,
    ) -> ResetPasswordUseCase:
        """Provide the reset password use case.

        Args:
            user_repository: User repository.
            jwt_service: JWT service.
            password_service: Password service.
            token_blocklist: Token blocklist.
            unit_of_work: Transaction boundary.

        Returns:
            ResetPasswordUseCase: Configured use case.
        """
        return ResetPasswordUseCase(
            user_repository, jwt_service, password_service, token_blocklist, unit_of_work
        )
