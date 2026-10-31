"""Отправка письма со ссылкой сброса пароля через SMTP.

Реализует порт `PasswordResetMailerInterface`: письмо содержит одноразовую ссылку,
сформированную сценарием, и не раскрывает ни текущий пароль, ни причину отказа.
"""

import asyncio
import smtplib
from email.message import EmailMessage

from backend.config import Settings
from backend.infrastructure.external._common import (
    ExternalServiceConfigurationError,
    ExternalServiceUnavailableError,
)
from backend.infrastructure.notifications.email.smtp_delivery import deliver_via_smtp


class PasswordResetMailer:
    """Отправляет письмо со ссылкой для сброса пароля."""

    async def send_reset_email(self, email: str, reset_link: str) -> None:
        """Отправляет письмо со ссылкой сброса на email пользователя."""
        if not Settings.smtp_host or not Settings.smtp_from_email:
            raise ExternalServiceConfigurationError(
                "SMTP settings are not configured", service_name="smtp"
            )

        message = EmailMessage()
        message["Subject"] = "Anime Epic Moments: сброс пароля"
        message["From"] = Settings.smtp_from_email
        message["To"] = email
        message.set_content(
            "Вы запросили сброс пароля для Anime Epic Moments.\n\n"
            f"Перейдите по ссылке, чтобы задать новый пароль:\n{reset_link}\n\n"
            f"Ссылка действует {Settings.password_reset_expire_minutes} минут."
        )

        try:
            await asyncio.to_thread(deliver_via_smtp, message)
        except (OSError, smtplib.SMTPException) as error:
            raise ExternalServiceUnavailableError(
                "Не удалось отправить письмо для сброса пароля. Проверьте SMTP-настройки и сетевой доступ.",
                service_name="smtp",
            ) from error
