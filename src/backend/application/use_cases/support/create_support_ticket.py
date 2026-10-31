"""Сценарий создания тикета поддержки."""

from __future__ import annotations

import logging

from starlette import status

from backend.application.dto import CreateSupportTicketCommand
from backend.application.interface.repositories.support_repository import SupportRepository
from backend.application.interface.services import (
    SupportEmailMailerInterface,
)
from backend.application.interface.services.telegram_support_notifier import (
    TelegramSupportNotifierInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.support.result import CreateSupportTicketResult
from backend.domain.entities.support.support_ticket import SupportTicket
from backend.domain.exceptions import DomainError


class CreateSupportTicketUseCase:
    """Создаёт тикет поддержки и отправляет его через выбранный канал."""

    _logger = logging.getLogger("anime_epic_moments")

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        telegram_notifier: TelegramSupportNotifierInterface,
        email_mailer: SupportEmailMailerInterface,
    ) -> None:
        """Инициализирует сценарий создания тикета поддержки.

        Args:
            unit_of_work: Граница транзакции Unit of Work.
            telegram_notifier: Сервис отправки уведомлений в Telegram.
            email_mailer: Сервис отправки писем по email.
        """
        self._unit_of_work = unit_of_work
        self._telegram_notifier = telegram_notifier
        self._email_mailer = email_mailer

    async def execute(self, command: CreateSupportTicketCommand) -> CreateSupportTicketResult:
        """Создать тикет поддержки.

        Порядок работы: сначала тикет сохраняется в собственной транзакции,
        затем отправляется во внешний канал, затем отдельной транзакцией
        фиксируется результат доставки. Сетевой вызов никогда не выполняется
        внутри открытой транзакции, поэтому соединение с базой не удерживается
        на время отправки в Telegram или SMTP.

        Args:
            command: Команда создания тикета.

        Returns:
            CreateSupportTicketResult: Созданный тикет и текст для показа.
        """
        try:
            ticket = SupportTicket.create(
                user_id=command.user_id,
                email=command.email,
                username=command.username,
                subject=command.subject,
                message=command.message,
                channel=command.channel,
                page_url=command.page_url,
            )
        except DomainError as error:
            return CreateSupportTicketResult.failure(
                str(error),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ticket = await self._store(ticket)
            service_unavailable = await self._deliver(ticket)
            ticket = await self._store_delivery_outcome(ticket)
        except DomainError as error:
            self._logger.error(
                "support_ticket_persist_failed user_id=%s error=%s",
                getattr(command, "user_id", None),
                error,
                exc_info=True,
            )
            return CreateSupportTicketResult.failure(
                "Не удалось создать тикет поддержки. Попробуй позже.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return CreateSupportTicketResult.success(
            data=ticket,
            message=self._success_message(ticket, service_unavailable),
            service_unavailable=service_unavailable,
        )

    async def _store(self, ticket: SupportTicket) -> SupportTicket:
        """Сохранить тикет в базе.

        Args:
            ticket: Тикет для сохранения.

        Returns:
            SupportTicket: Сохранённый тикет с присвоенным идентификатором.
        """
        async with self._unit_of_work as uow:
            return await uow.repository(SupportRepository).add(ticket)

    async def _store_delivery_outcome(self, ticket: SupportTicket) -> SupportTicket:
        """Зафиксировать результат доставки тикета.

        Args:
            ticket: Тикет с проставленным статусом доставки.

        Returns:
            SupportTicket: Сохранённый тикет.
        """
        async with self._unit_of_work as uow:
            return await uow.repository(SupportRepository).update(ticket)

    async def _deliver(self, ticket: SupportTicket) -> bool:
        """Отправить тикет во внешний канал.

        Args:
            ticket: Сохранённый тикет.

        Returns:
            bool: True, если канал временно недоступен.
        """
        try:
            await self._delivery_provider(ticket.channel).send_ticket_created(ticket)
            ticket.mark_delivered()
        except RuntimeError as error:
            ticket.mark_delivery_failed(str(error))
            return True
        return False

    def _delivery_provider(self, channel: str):
        """Вернуть сервис доставки для выбранного канала.

        Args:
            channel: Канал доставки, уже проверенный доменной политикой.

        Returns:
            TelegramSupportNotifierInterface | SupportEmailMailerInterface: Сервис доставки.
        """
        if channel == "telegram":
            return self._telegram_notifier
        return self._email_mailer

    def _success_message(self, ticket: SupportTicket, service_unavailable: bool) -> str:
        """Собрать текст успешного ответа по результату доставки.

        Args:
            ticket: Созданный тикет.
            service_unavailable: Был ли канал временно недоступен.

        Returns:
            str: Текст для показа пользователю.
        """
        if not service_unavailable:
            return (
                "Тикет отправлен в поддержку через Telegram."
                if ticket.channel == "telegram"
                else "Тикет отправлен в поддержку по email."
            )
        return (
            "Тикет сохранен, но Telegram сейчас недоступен. Поддержка сможет забрать его позже."
            if ticket.channel == "telegram"
            else "Тикет сохранен, но email-канал сейчас недоступен. Поддержка сможет забрать его позже."
        )
