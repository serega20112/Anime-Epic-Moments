"""Отправители уведомлений: почтовые мейлеры, Telegram-оповещение и хранилище токенов верификации."""

from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from backend.config import Settings
from backend.infrastructure.cache.security_store import SecurityKeyValueStore
from backend.infrastructure.notifications import TelegramSupportNotifier
from backend.infrastructure.notifications.email import (
    EmailVerificationMailer,
    PasswordResetMailer,
    SupportEmailMailer,
)
from backend.infrastructure.security.email_verification_store import EmailVerificationStore


class NotificationProvidersMixin(Provider):
    """Отправители уведомлений: почтовые мейлеры, Telegram-оповещение и хранилище токенов верификации.

    Часть провайдера: методы `@provide` собираются dishka из базовых
    классов, поэтому mixin самодостаточен и наследует `Provider`.
    """

    @provide(scope=Scope.APP)
    async def password_reset_mailer(self) -> PasswordResetMailer:
        """Создать отправителя писем сброса пароля."""
        return PasswordResetMailer()

    @provide(scope=Scope.APP)
    async def email_verification_mailer(self) -> EmailVerificationMailer:
        """Создать отправителя писем подтверждения почты."""
        return EmailVerificationMailer()

    @provide(scope=Scope.APP)
    async def telegram_support_notifier(self) -> AsyncIterator[TelegramSupportNotifier]:
        """Создать уведомитель поддержки в Telegram."""
        notifier = TelegramSupportNotifier()
        yield notifier
        await notifier.aclose()

    @provide(scope=Scope.APP)
    async def support_email_mailer(self) -> SupportEmailMailer:
        """Создать отправителя писем поддержки."""
        return SupportEmailMailer()

    @provide(scope=Scope.APP)
    async def email_verification_store(
        self, store: SecurityKeyValueStore
    ) -> EmailVerificationStore:
        """Создать хранилище кодов подтверждения почты."""
        return EmailVerificationStore(
            store=store,
            ttl_seconds=Settings.email_verification_expire_minutes * 60,
        )
