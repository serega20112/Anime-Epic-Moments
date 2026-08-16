import smtplib
from email.message import EmailMessage

from backend.config import Settings
from backend.infrastructure.external._async import external_method
from backend.infrastructure.external.errors import (
    ExternalServiceConfigurationError,
    ExternalServiceUnavailableError,
)


class PasswordResetMailer:
    """Отправляет письмо со ссылкой для сброса пароля."""

    @external_method
    def send_reset_email(self, email: str, reset_link: str) -> None:
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
            with smtplib.SMTP(Settings.smtp_host, Settings.smtp_port, timeout=30) as smtp:
                if Settings.smtp_use_tls:
                    smtp.starttls()
                if Settings.smtp_username and Settings.smtp_password:
                    smtp.login(Settings.smtp_username, Settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise ExternalServiceUnavailableError(
                "Не удалось отправить письмо для сброса пароля. Проверь SMTP-настройки и сетевой доступ.",
                service_name="smtp",
            ) from error
