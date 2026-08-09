from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from backend.application.dto import CreateSupportTicketCommand
from backend.application.use_cases.support.result import CreateSupportTicketResult
from backend.domain import is_support_channel, normalize_support_channel
from backend.domain.repositories.support_repository import SupportRepository
from backend.domain.services import (
    SupportEmailMailerInterface as SupportEmailMailer,
)
from backend.domain.services.telegram_support_notifier import (
    TelegramSupportNotifierInterface as TelegramSupportNotifier,
)
from backend.domain.support.entity import SupportTicket


class CreateSupportTicketUseCase:
    """Создает тикет поддержки и отправляет его через выбранный канал."""

    _logger = logging.getLogger("anime_epic_moments")

    def __init__(
            self,
            support_repo: SupportRepository,
            telegram_notifier: TelegramSupportNotifier,
            email_mailer: SupportEmailMailer,
    ):
        self.support_repo = support_repo
        self.telegram_notifier = telegram_notifier
        self.email_mailer = email_mailer

    async def execute(self, command: CreateSupportTicketCommand) -> CreateSupportTicketResult:
        """Валидирует тикет, сохраняет его и отправляет через один выбранный канал.

        Args:
            command: Create support ticket command.

        Returns:
            CreateSupportTicketResult: Outcome with the created ticket or a message.
        """
        try:
            return await self._run(command)
        except Exception as error:
            self._logger.error(
                "support_ticket_create_failed user_id=%s error=%s",
                getattr(command, "user_id", None),
                error,
                exc_info=True,
            )
            return CreateSupportTicketResult.failure(
                "Не удалось создать тикет поддержки. Попробуй позже.",
                status_code=500,
            )

    async def _run(self, command: CreateSupportTicketCommand) -> CreateSupportTicketResult:
        normalized_email = self._normalize_email(command.email)
        normalized_username = self._normalize_username(command.username)
        normalized_subject = self._normalize_subject(command.subject)
        normalized_message = self._normalize_message(command.message)
        normalized_channel = self._normalize_channel(command.channel)
        normalized_page_url = self._normalize_page_url(command.page_url)

        try:
            self._validate_email(normalized_email)
            self._validate_username(normalized_username)
            self._validate_subject(normalized_subject)
            self._validate_message(normalized_message)
            self._validate_channel(normalized_channel)
            self._validate_page_url(normalized_page_url)
        except InvalidSupportTicketError as error:
            return CreateSupportTicketResult.failure(str(error), status_code=400)

        ticket = await self.support_repo.add(
            SupportTicket(
                user_id=command.user_id,
                email=normalized_email,
                username=normalized_username,
                subject=normalized_subject,
                message=normalized_message,
                channel=normalized_channel,
                page_url=normalized_page_url,
            )
        )

        service_unavailable = False
        try:
            await self._delivery_provider(normalized_channel).send_ticket_created(ticket)
            ticket.mark_delivered()
        except RuntimeError as error:
            ticket.mark_delivery_failed(str(error))
            service_unavailable = True

        ticket = await self.support_repo.update(ticket)
        return CreateSupportTicketResult.success(
            data=ticket,
            message=self._success_message(ticket, service_unavailable),
            service_unavailable=service_unavailable,
        )

    def _success_message(self, ticket: SupportTicket, service_unavailable: bool) -> str:
        """Build the success flash message from the delivery outcome.

        Args:
            ticket: Created ticket.
            service_unavailable: Whether delivery failed due to a down channel.

        Returns:
            str: User-facing success message.
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

    def _normalize_email(self, value: str | None) -> str:
        """Нормализует email пользователя."""
        return str(value or "").strip().lower()

    def _normalize_username(self, value: str | None) -> str:
        """Нормализует username пользователя."""
        return " ".join(str(value or "").strip().split())

    def _normalize_subject(self, value: str | None) -> str:
        """Нормализует тему тикета."""
        return " ".join(str(value or "").strip().split())

    def _normalize_message(self, value: str | None) -> str:
        """Очищает текст обращения, сохраняя переводы строк."""
        lines = [line.rstrip() for line in str(value or "").strip().splitlines()]
        return "\n".join(lines).strip()

    def _normalize_channel(self, value: str | None) -> str:
        """Нормализует код канала доставки support-тикета."""
        return str(value or "").strip().lower()

    def _normalize_page_url(self, value: str | None) -> str | None:
        """Нормализует адрес страницы, где возникла проблема."""
        normalized = str(value or "").strip()
        return normalized or None

    def _validate_email(self, value: str) -> None:
        """Проверяет корректность email пользователя."""
        if len(value) > 254:
            raise InvalidSupportTicketError("Email слишком длинный")
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, value):
            raise InvalidSupportTicketError("Некорректный email")

    def _validate_username(self, value: str) -> None:
        """Проверяет корректность имени пользователя."""
        if not value or len(value) > 40:
            raise InvalidSupportTicketError("Укажи имя или ник длиной до 40 символов")

    def _validate_subject(self, value: str) -> None:
        """Проверяет тему тикета."""
        if not value or len(value) < 4 or len(value) > 120:
            raise InvalidSupportTicketError("Тема должна быть от 4 до 120 символов")

    def _validate_message(self, value: str) -> None:
        """Проверяет текст обращения в поддержку."""
        if not value or len(value) < 10 or len(value) > 4000:
            raise InvalidSupportTicketError("Сообщение должно быть от 10 до 4000 символов")

    def _validate_channel(self, value: str) -> None:
        """Проверяет допустимость выбранного канала доставки."""
        if not is_support_channel(value):
            raise InvalidSupportTicketError("Выбери способ отправки тикета")

    def _validate_page_url(self, value: str | None) -> None:
        """Проверяет, что page_url пустой, относительный или http(s)-адрес."""
        if value is None:
            return
        if len(value) > 500:
            raise InvalidSupportTicketError("Адрес страницы слишком длинный")
        if value.startswith("/"):
            return
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidSupportTicketError("Укажи корректный адрес страницы")

    def _delivery_provider(self, channel: str):
        """Возвращает сервис доставки для выбранного support-канала."""
        if channel == "telegram":
            return self.telegram_notifier
        return self.email_mailer
