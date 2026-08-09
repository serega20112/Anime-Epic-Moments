from datetime import datetime


class SupportTicket:
    """Агрегат тикета поддержки."""

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
        self.created_at = created_at or datetime.utcnow()

    def mark_delivered(self) -> None:
        """Помечает тикет как доставленный через выбранный канал."""
        self.delivery_status = "sent"
        self.delivery_error = None

    def mark_delivery_failed(self, error_message: str) -> None:
        """Помечает тикет как недоставленный и сохраняет причину."""
        self.delivery_status = "failed"
        normalized_error = str(error_message or "").strip()
        self.delivery_error = normalized_error[:500] if normalized_error else "unknown"
