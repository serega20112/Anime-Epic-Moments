"""Провайдеры сценариев аутентификации и аккаунта."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.services import GoogleAuthClientInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.policies import PasswordResetPolicy
from backend.application.use_cases import (
    GoogleSignInUseCase,
    LinkGoogleAccountUseCase,
    LogoutUserUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
    RequestEmailVerificationUseCase,
    RequestPasswordResetUseCase,
    ResendEmailVerificationUseCase,
    UnlinkGoogleAccountUseCase,
    UpdateUserProfileUseCase,
    VerifyEmailUseCase,
)
from backend.application.use_cases.auth.login_register.login_user import LoginUserUseCase
from backend.application.use_cases.auth.password_reset.reset_password import ResetPasswordUseCase
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.notifications.email import (
    EmailVerificationMailer,
    PasswordResetMailer,
)
from backend.infrastructure.security.account_lock_service import AccountLockService
from backend.infrastructure.security.email_verification_store import EmailVerificationStore
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.password_service import PasswordService
from backend.infrastructure.security.token_blocklist import TokenBlocklist


class AuthUseCaseProvider(Provider):
    """Провайдер сценариев входа, регистрации и аккаунта."""

    @provide(scope=Scope.REQUEST)
    async def register_user(
        self,
        unit_of_work: UnitOfWorkInterface,
        password_service: PasswordService,
    ) -> RegisterUserUseCase:
        """Создать сценарий регистрации пользователя."""
        return RegisterUserUseCase(unit_of_work, password_service)

    @provide(scope=Scope.REQUEST)
    async def request_email_verification(
        self,
        unit_of_work: UnitOfWorkInterface,
        password_service: PasswordService,
        email_verification_store: EmailVerificationStore,
        email_verification_mailer: EmailVerificationMailer,
    ) -> RequestEmailVerificationUseCase:
        """Создать сценарий запроса подтверждения почты."""
        return RequestEmailVerificationUseCase(
            unit_of_work,
            password_service,
            email_verification_store,
            email_verification_mailer,
        )

    @provide(scope=Scope.REQUEST)
    async def resend_email_verification(
        self,
        email_verification_store: EmailVerificationStore,
        email_verification_mailer: EmailVerificationMailer,
    ) -> ResendEmailVerificationUseCase:
        """Создать сценарий повторной отправки кода подтверждения."""
        return ResendEmailVerificationUseCase(
            email_verification_store,
            email_verification_mailer,
        )

    @provide(scope=Scope.REQUEST)
    async def verify_email(
        self,
        unit_of_work: UnitOfWorkInterface,
        email_verification_store: EmailVerificationStore,
    ) -> VerifyEmailUseCase:
        """Создать сценарий подтверждения почты."""
        return VerifyEmailUseCase(unit_of_work, email_verification_store)

    @provide(scope=Scope.REQUEST)
    async def login_user(
        self,
        unit_of_work: UnitOfWorkInterface,
        password_service: PasswordService,
        account_lock_service: AccountLockService,
    ) -> LoginUserUseCase:
        """Создать сценарий входа."""
        return LoginUserUseCase(unit_of_work, password_service, account_lock_service)

    @provide(scope=Scope.REQUEST)
    async def logout_user(
        self,
        jwt_service: JWTService,
        token_blocklist: TokenBlocklist,
    ) -> LogoutUserUseCase:
        """Создать сценарий выхода."""
        return LogoutUserUseCase(jwt_service, token_blocklist)

    @provide(scope=Scope.REQUEST)
    async def refresh_session(
        self,
        jwt_service: JWTService,
        token_blocklist: TokenBlocklist,
        unit_of_work: UnitOfWorkInterface,
    ) -> RefreshSessionUseCase:
        """Создать сценарий продления сессии."""
        return RefreshSessionUseCase(jwt_service, token_blocklist, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def update_user_profile(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> UpdateUserProfileUseCase:
        """Создать сценарий правки профиля."""
        return UpdateUserProfileUseCase(unit_of_work, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    async def request_password_reset(
        self,
        unit_of_work: UnitOfWorkInterface,
        jwt_service: JWTService,
        password_reset_mailer: PasswordResetMailer,
        policy: PasswordResetPolicy,
    ) -> RequestPasswordResetUseCase:
        """Создать сценарий запроса сброса пароля.

        Args:
            unit_of_work: Граница транзакции чтения пользователя.
            jwt_service: Сервис JWT-токенов.
            password_reset_mailer: Почтовый сервис ссылок восстановления.
            policy: Узкая политика сброса пароля.

        Returns:
            RequestPasswordResetUseCase: Настроенный сценарий.
        """
        return RequestPasswordResetUseCase(
            unit_of_work,
            jwt_service,
            password_reset_mailer,
            policy,
        )

    @provide(scope=Scope.REQUEST)
    async def reset_password(
        self,
        unit_of_work: UnitOfWorkInterface,
        jwt_service: JWTService,
        password_service: PasswordService,
        token_blocklist: TokenBlocklist,
    ) -> ResetPasswordUseCase:
        """Создать сценарий сброса пароля."""
        return ResetPasswordUseCase(unit_of_work, jwt_service, password_service, token_blocklist)

    @provide(scope=Scope.REQUEST)
    async def google_sign_in(
        self,
        unit_of_work: UnitOfWorkInterface,
        google_client: GoogleAuthClientInterface,
        password_service: PasswordService,
    ) -> GoogleSignInUseCase:
        """Создать сценарий входа через Google."""
        return GoogleSignInUseCase(unit_of_work, google_client, password_service)

    @provide(scope=Scope.REQUEST)
    async def link_google_account(
        self,
        unit_of_work: UnitOfWorkInterface,
        google_client: GoogleAuthClientInterface,
    ) -> LinkGoogleAccountUseCase:
        """Создать сценарий привязки аккаунта Google."""
        return LinkGoogleAccountUseCase(unit_of_work, google_client)

    @provide(scope=Scope.REQUEST)
    async def unlink_google_account(
        self, unit_of_work: UnitOfWorkInterface
    ) -> UnlinkGoogleAccountUseCase:
        """Создать сценарий отвязки аккаунта Google."""
        return UnlinkGoogleAccountUseCase(unit_of_work)
