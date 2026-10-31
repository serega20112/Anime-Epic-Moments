"""Почтовые реализации портов уведомлений.

Здесь живут отправки писем через SMTP: подтверждение адреса, сброс пароля и
пересылка тикета поддержки. Формат письма и подключение к серверу — деталь
инфраструктуры; сценарии работают с интерфейсами из application-слоя.
"""

from __future__ import annotations

from .email_verification_mailer import EmailVerificationMailer
from .password_reset_mailer import PasswordResetMailer
from .support_email_mailer import SupportEmailMailer

__all__ = [
    "EmailVerificationMailer",
    "PasswordResetMailer",
    "SupportEmailMailer",
]
