"""Провайдеры сценариев поддержки."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases import CreateSupportTicketUseCase
from backend.infrastructure.notifications import TelegramSupportNotifier
from backend.infrastructure.notifications.email import SupportEmailMailer


class SupportUseCaseProvider(Provider):
    """Провайдер сценариев поддержки."""

    @provide(scope=Scope.REQUEST)
    async def create_support_ticket(
        self,
        unit_of_work: UnitOfWorkInterface,
        telegram_support_notifier: TelegramSupportNotifier,
        support_email_mailer: SupportEmailMailer,
    ) -> CreateSupportTicketUseCase:
        """Создать сценарий обращения в поддержку."""
        return CreateSupportTicketUseCase(
            unit_of_work,
            telegram_support_notifier,
            support_email_mailer,
        )
