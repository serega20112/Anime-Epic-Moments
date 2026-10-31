"""Агрегат тикета поддержки."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.domain.policies.support_ticket_policy import (
    normalize_page_url,
    normalize_support_email,
    normalize_support_username,
    validate_support_channel,
    validate_support_email,
    validate_support_message,
    validate_support_subject,
    validate_support_username,
)

DELIVERY_ERROR_MAX_LENGTH = 500


class SupportTicket:
    """Агрегат тикета поддержки.

    Тикет — единственная сущность, работающая с недоверенным пользовательским
    вводом, поэтому нормализация и проверки формата выполняются в
    :meth:`create`, а не в вызывающем коде.
    """

    def __init__(
        self,
        email: str,
        username: str,
        subject: str,
        message: str,
        channel: str = "telegram",
        user_id: int | None = None,
        page_url: str | None = None,
        status: str = "open",
        delivery_status: str = "pending",
        delivery_error: str | None = None,
        created_at: datetime | None = None,
        id: int | None = None,
    ):
        """Создать тикет поддержки.

        Args:
            email: Email для ответа.
            username: Имя пользователя.
            subject: Тема обращения.
            message: Текст обращения.
            channel: Канал доставки.
            user_id: Идентификатор автора либо None для гостя.
            page_url: Адрес страницы, с которой отправлен тикет.
            status: Статус тикета.
            delivery_status: Статус доставки.
            delivery_error: Причина недоставки.
            created_at: Время создания, по умолчанию текущее UTC.
            id: Идентификатор, присваивается хранилищем.
        """
        self.id = id
        self.user_id = user_id
        self.email = email
        self.username = username
        self.subject = subject
        self.message = message
        self.channel = channel
        self.page_url = page_url
        self.status = status
        self.delivery_status = delivery_status
        self.delivery_error = delivery_error
        self.created_at = created_at or datetime.now(UTC)

    @classmethod
    def create(
        cls,
        *,
        email: str,
        username: str,
        subject: str,
        message: str,
        channel: str = "telegram",
        user_id: int | None = None,
        page_url: str | None = None,
    ) -> SupportTicket:
        """Создать тикет, применив правила нормализации и проверки формата.

        Args:
            email: Email для ответа.
            username: Имя пользователя.
            subject: Тема обращения.
            message: Текст обращения.
            channel: Канал доставки.
            user_id: Идентификатор автора либо None для гостя.
            page_url: Адрес страницы, с которой отправлен тикет.

        Returns:
            SupportTicket: Валидный тикет поддержки.

        Raises:
        ValidationError: Любое поле не соответствует доменным правилам.
        """
        normalized_email = normalize_support_email(email)
        normalized_username = normalize_support_username(username)
        validate_support_email(normalized_email)
        validate_support_username(normalized_username)
        validate_support_subject(str(subject or "").strip())
        validate_support_message(str(message or "").strip())
        return cls(
            user_id=user_id,
            email=normalized_email,
            username=normalized_username,
            subject=str(subject or "").strip(),
            message=str(message or "").strip(),
            channel=validate_support_channel(channel),
            page_url=normalize_page_url(page_url),
        )

    def mark_delivered(self) -> None:
        """Помечает тикет как доставленный через выбранный канал."""
        self.delivery_status = "sent"
        self.delivery_error = None

    def mark_delivery_failed(self, error_message: str) -> None:
        """Помечает тикет как недоставленный и сохраняет причину.

        Args:
            error_message: Текст ошибки доставки.
        """
        self.delivery_status = "failed"
        normalized_error = str(error_message or "").strip()
        self.delivery_error = (
            normalized_error[:DELIVERY_ERROR_MAX_LENGTH] if normalized_error else "unknown"
        )
