from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.infrastructure.external import password_reset_mailer as mailer_module
from src.backend.infrastructure.external.password_reset_mailer import PasswordResetMailer


class _FakeSMTP:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.started_tls = False
        self.logged_in = None
        self.message = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.logged_in = (username, password)

    def send_message(self, message):
        self.message = message


def test_password_reset_mailer_requires_smtp_settings(monkeypatch):
    """Проверяем, что PasswordResetMailer падает без обязательных SMTP-настроек."""
    monkeypatch.setattr(
        mailer_module,
        "Settings",
        SimpleNamespace(
            smtp_host=None,
            smtp_port=587,
            smtp_username=None,
            smtp_password=None,
            smtp_from_email=None,
            smtp_use_tls=True,
            password_reset_expire_minutes=30,
        ),
    )

    with pytest.raises(RuntimeError):
        PasswordResetMailer().send_reset_email("user@example.com", "http://example.com/reset")


def test_password_reset_mailer_sends_message_with_tls_and_login(monkeypatch):
    """Проверяем, что PasswordResetMailer формирует письмо и использует TLS/login при наличии настроек."""
    smtp_instance = _FakeSMTP()
    monkeypatch.setattr(mailer_module.smtplib, "SMTP", lambda *args, **kwargs: smtp_instance)
    monkeypatch.setattr(
        mailer_module,
        "Settings",
        SimpleNamespace(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="mailer",
            smtp_password="secret",
            smtp_from_email="noreply@example.com",
            smtp_use_tls=True,
            password_reset_expire_minutes=30,
        ),
    )

    PasswordResetMailer().send_reset_email(
        "user@example.com",
        "http://example.com/reset?token=abc",
    )

    assert smtp_instance.started_tls is True
    assert smtp_instance.logged_in == ("mailer", "secret")
    assert smtp_instance.message["To"] == "user@example.com"
    assert "http://example.com/reset?token=abc" in smtp_instance.message.get_content()


def test_password_reset_mailer_wraps_network_errors(monkeypatch):
    """Проверяем, что PasswordResetMailer превращает сетевой сбой SMTP в RuntimeError."""
    monkeypatch.setattr(
        mailer_module.smtplib,
        "SMTP",
        lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("timeout")),
    )
    monkeypatch.setattr(
        mailer_module,
        "Settings",
        SimpleNamespace(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="mailer",
            smtp_password="secret",
            smtp_from_email="noreply@example.com",
            smtp_use_tls=True,
            password_reset_expire_minutes=30,
        ),
    )

    with pytest.raises(RuntimeError, match="Не удалось отправить письмо для сброса пароля"):
        PasswordResetMailer().send_reset_email("user@example.com", "http://example.com/reset")
