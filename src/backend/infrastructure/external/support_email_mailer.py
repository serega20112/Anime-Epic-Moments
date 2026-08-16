import smtplib
from email.message import EmailMessage

from backend.config import Settings
from backend.domain.support.entity import SupportTicket
from backend.infrastructure.external._async import external_method
from backend.infrastructure.external.errors import (
    ExternalServiceConfigurationError,
    ExternalServiceUnavailableError,
)


class SupportEmailMailer:
    """Отправляет тикеты поддержки на email команды."""

    def __init__(self):
        self.recipient_emails = Settings.support_email_to

    def is_enabled(self) -> bool:
        """Возвращает доступность email-канала поддержки по текущей конфигурации."""
        return bool(Settings.smtp_host and Settings.smtp_from_email and self.recipient_emails)

    @external_method
    def send_ticket_created(self, ticket: SupportTicket) -> int:
        """Отправляет тикет поддержки по email во все настроенные адреса."""
        if not self.is_enabled():
            raise ExternalServiceConfigurationError(
                "Support email delivery is not configured", service_name="smtp"
            )

        message = EmailMessage()
        message["Subject"] = self._build_subject(ticket)
        message["From"] = Settings.smtp_from_email
        message["To"] = ", ".join(self.recipient_emails)
        if ticket.email:
            message["Reply-To"] = ticket.email
        message.set_content(self._build_plain_text(ticket))

        try:
            with smtplib.SMTP(Settings.smtp_host, Settings.smtp_port, timeout=30) as smtp:
                if Settings.smtp_use_tls:
                    smtp.starttls()
                if Settings.smtp_username and Settings.smtp_password:
                    smtp.login(Settings.smtp_username, Settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise ExternalServiceUnavailableError(
                "Не удалось отправить тикет по email. Проверь SMTP и SUPPORT_EMAIL_TO.",
                service_name="smtp",
            ) from error

        return len(self.recipient_emails)

    def _build_subject(self, ticket: SupportTicket) -> str:
        """Формирует тему письма support-тикета."""
        subject = " ".join(str(ticket.subject or "").split())
        safe_subject = subject[:120] if len(subject) > 120 else subject
        return f"AEM support #{ticket.id}: {safe_subject}"

    def _build_plain_text(self, ticket: SupportTicket) -> str:
        """Собирает plain-text тело письма для нового тикета."""
        created_at = ticket.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            "Новый тикет поддержки Anime Epic Moments",
            "",
            f"ID: {ticket.id}",
            f"Канал: {ticket.channel}",
            f"Пользователь: {ticket.username}",
            f"Email: {ticket.email}",
            f"User ID: {ticket.user_id if ticket.user_id is not None else 'guest'}",
            f"Тема: {ticket.subject}",
            f"Создан: {created_at}",
        ]
        if ticket.page_url:
            lines.append(f"Страница: {ticket.page_url}")
        lines.extend(["", "Сообщение:", ticket.message])
        return "\n".join(lines)
