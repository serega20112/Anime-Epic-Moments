"""Support use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.use_cases import CreateSupportTicketUseCase
from backend.domain.unit_of_work import UnitOfWorkInterface
from backend.infrastructure.external import SupportEmailMailer, TelegramSupportNotifier
from backend.infrastructure.repositories.support_repository import SupportRepository


class SupportUseCaseProvider(Provider):
    """Provide support use cases."""

    @provide(scope=Scope.REQUEST)
    def create_support_ticket(
        self,
        support_repository: SupportRepository,
        telegram_support_notifier: TelegramSupportNotifier,
        support_email_mailer: SupportEmailMailer,
        unit_of_work: UnitOfWorkInterface,
    ) -> CreateSupportTicketUseCase:
        """Provide the create support ticket use case.

        Args:
            support_repository: Support repository.
            telegram_support_notifier: Telegram notifier.
            support_email_mailer: Support email mailer.
            unit_of_work: Transaction boundary.

        Returns:
            CreateSupportTicketUseCase: Configured use case.
        """
        return CreateSupportTicketUseCase(
            support_repository,
            telegram_support_notifier,
            support_email_mailer,
            unit_of_work,
        )
