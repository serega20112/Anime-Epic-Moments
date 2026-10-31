"""Общая SMTP-доставка писем для почтовых адаптеров."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from backend.config import Settings


def deliver_via_smtp(message: EmailMessage) -> None:
    """Отправить письмо через SMTP; вызов блокирующий.

    В стандартной библиотеке нет асинхронного SMTP-клиента, поэтому отправку
    поднимают в :func:`asyncio.to_thread`. Хост, порт, TLS и учётные данные
    читаются здесь один раз: у всех почтовых сценариев один транспорт, и
    разнобой в настройках проявился бы только на проде.

    Args:
        message: Готовое письмо с заголовками и телом.

    Raises:
        OSError: Если сетевой доступ к SMTP-серверу невозможен.
        smtplib.SMTPException: Если сервер отклонил протокольный шаг.
    """
    with smtplib.SMTP(Settings.smtp_host, Settings.smtp_port, timeout=30) as smtp:
        if Settings.smtp_use_tls:
            smtp.starttls()
        if Settings.smtp_username and Settings.smtp_password:
            smtp.login(Settings.smtp_username, Settings.smtp_password)
        smtp.send_message(message)
