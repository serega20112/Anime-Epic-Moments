"""Структурированное логирование и журнал событий безопасности.

Формат вывода выбирается переменной окружения ``LOG_FORMAT``: ``json`` для
прода (строки разбираются лог-агрегатором) и ``text`` для локальной разработки,
где человек читает консоль глазами. Timestamp всегда в UTC и с суффиксом ``Z``,
чтобы не путать локальное время хостинга и время приложения.
"""

from __future__ import annotations

import logging
import os
import re
import sys
import time
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger.json import JsonFormatter

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)

LOG_FORMAT_JSON = "json"
LOG_FORMAT_TEXT = "text"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
JSON_LAYOUT = "%(asctime)s %(levelname)s %(name)s %(request_id)s %(user_id)s %(message)s"
TEXT_LAYOUT = "%(asctime)s %(levelname)-7s %(request_id)s %(user_id)s %(name)s: %(message)s"
NOISY_LOGGERS = ("httpx", "httpcore", "urllib3", "websockets", "asyncio")
ACCESS_LOGGERS = ("uvicorn.access", "gunicorn.access")
MASKED_PLACEHOLDER = "***"
SECRET_QUERY_PATTERN = re.compile(
    r"(?i)\b(token|api_key|apikey|secret|password|passwd|pwd|auth|access_token|refresh_token|key)"
    r"(=|:)\s*[^&\s\"']+"
)
CREDENTIAL_PATTERN = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{6,}")
EMAIL_PATTERN = re.compile(r"(?i)\b[\w.+-]+(@[\w-]+\.[\w.-]+)")


class RequestIdFilter(logging.Filter):
    """Добавляет идентификатор запроса и пользователя в записи журнала.

    Значения берутся из контекстных переменных, которые заполняет middleware
    логирования запросов; при их отсутствии подставляются значения по умолчанию.
    """

    def __init__(self) -> None:
        """Создать фильтр с пустыми значениями по умолчанию."""
        super().__init__()
        self.request_id: str | None = None
        self.user_id: str | None = None

    def filter(self, record: logging.LogRecord) -> bool:
        """Добавить контекст запроса и пользователя в запись журнала."""
        record.request_id = request_id_var.get() or self.request_id or "-"
        record.user_id = user_id_var.get() or self.user_id or "-"
        return True


class SecretMaskFilter(logging.Filter):
    """Маскирует креды, токены и адреса почты в тексте записей журнала.

    Сторонние библиотеки (httpx, провайдеры видео) печатают полные URL с
    параметрами ``token`` и ``key``, поэтому секреты не должны попадать в
    логи хостинга.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Заменить чувствительные фрагменты уже отформатированного сообщения."""
        record.msg = mask_secrets(record.getMessage())
        record.args = None
        return True


def mask_secrets(text: str) -> str:
    """Скрыть токены, креды и адреса почты в произвольном тексте.

    Args:
        text: Исходный текст записи журнала.

    Returns:
        str: Текст с замаскированными чувствительными фрагментами.
    """
    masked = SECRET_QUERY_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{MASKED_PLACEHOLDER}", text
    )
    masked = CREDENTIAL_PATTERN.sub(lambda match: f"{match.group(1)} {MASKED_PLACEHOLDER}", masked)
    return EMAIL_PATTERN.sub(lambda match: f"***{match.group(1)}", masked)


def build_formatter(fmt: str) -> logging.Formatter:
    """Построить форматтер записей журнала выбранного формата.

    Args:
        fmt: ``json`` для структурированного вывода либо ``text`` для консоли.

    Returns:
        logging.Formatter: Форматтер с временем в UTC.
    """
    if fmt.strip().lower() == LOG_FORMAT_JSON:
        formatter: logging.Formatter = JsonFormatter(
            JSON_LAYOUT,
            datefmt=TIMESTAMP_FORMAT,
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        )
    else:
        formatter = logging.Formatter(TEXT_LAYOUT, datefmt=TIMESTAMP_FORMAT)
    formatter.converter = time.gmtime
    return formatter


def _quiet_third_party_loggers() -> None:
    """Приглушить шум библиотек и дубль доступа: своё уже пишет middleware."""
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    for name in ACCESS_LOGGERS:
        logging.getLogger(name).disabled = True


def setup_logging(*, level: int = logging.INFO, fmt: str = LOG_FORMAT_JSON) -> None:
    """Настроить корневой логгер на структурированный вывод.

    Args:
        level: Минимальный уровень записей.
        fmt: ``json`` либо ``text``.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(build_formatter(fmt))
    handler.addFilter(RequestIdFilter())
    handler.addFilter(SecretMaskFilter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    _quiet_third_party_loggers()


def get_audit_logger() -> logging.Logger:
    """Вернуть отдельный логгер событий безопасности.

    Returns:
        logging.Logger: Логгер аудита с собственным обработчиком вывода.
    """
    logger = logging.getLogger("security.audit")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(build_formatter(os.getenv("LOG_FORMAT", LOG_FORMAT_JSON)))
        handler.addFilter(SecretMaskFilter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def log_business_event(
    *,
    event: str,
    user_id: str | int | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Записать бизнес-событие в журнал аудита.

    Args:
        event: Имя события.
        user_id: Идентификатор пользователя, если он известен.
        ip_address: Адрес клиента.
        details: Дополнительные поля события.
    """
    audit_logger = get_audit_logger()
    payload: dict[str, Any] = {"event": event}
    if user_id is not None:
        payload["user_id"] = str(user_id)
    if ip_address:
        payload["ip_address"] = ip_address
    if details:
        payload.update(details)
    audit_logger.info("business_event", extra={"business_event": payload})


def log_security_event(
    *,
    event: str,
    user_id: str | None = None,
    email: str | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Записать событие безопасности в журнал аудита.

    Args:
        event: Имя события.
        user_id: Идентификатор пользователя, если он известен.
        email: Адрес электронной почты из сценария.
        ip_address: Адрес клиента.
        details: Дополнительные поля события.
    """
    audit_logger = get_audit_logger()
    payload: dict[str, Any] = {"event": event}
    if user_id:
        payload["user_id"] = user_id
    if email:
        payload["email"] = email
    if ip_address:
        payload["ip_address"] = ip_address
    if details:
        payload.update(details)
    audit_logger.info("security_event", extra={"security_event": payload})
