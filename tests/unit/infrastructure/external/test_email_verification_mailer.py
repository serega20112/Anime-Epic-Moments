from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.infrastructure.external import email_verification_mailer as mailer_module
from backend.infrastructure.external.email_verification_mailer import (
    EmailVerificationMailer,
)


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


def test_email_verification_mailer_requires_smtp_settings(monkeypatch):
    """Проверяем, что EmailVerificationMailer падает без обязательных SMTP-настроек."""
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
            email_verification_expire_minutes=10,
        ),
    )

    with pytest.raises(RuntimeError):
        EmailVerificationMailer().send_verification_code("user@example.com", "123456")


def test_email_verification_mailer_sends_message_with_tls_and_login(monkeypatch):
    """Проверяем, что EmailVerificationMailer формирует письмо и использует TLS/login при наличии настроек."""
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
            email_verification_expire_minutes=10,
        ),
    )

    EmailVerificationMailer().send_verification_code(
        "user@example.com",
        "123456",
        theme="dark",
    )

    assert smtp_instance.started_tls is True
    assert smtp_instance.logged_in == ("mailer", "secret")
    assert smtp_instance.message["To"] == "user@example.com"
    plain_part = smtp_instance.message.get_body(preferencelist=("plain",))
    assert plain_part is not None
    assert "123456" in plain_part.get_content()
    html_part = smtp_instance.message.get_body(preferencelist=("html",))
    assert html_part is not None
    assert "Тёмная тема" in html_part.get_content()
    assert "#050505" in html_part.get_content()


def test_email_verification_mailer_wraps_network_errors(monkeypatch):
    """Проверяем, что EmailVerificationMailer превращает сетевой сбой SMTP в RuntimeError."""
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
            email_verification_expire_minutes=10,
        ),
    )

    with pytest.raises(RuntimeError, match="Не удалось отправить письмо с кодом подтверждения"):
        EmailVerificationMailer().send_verification_code("user@example.com", "123456")


@pytest.mark.parametrize(
    ("theme", "expected_fragment"),
    [
        ("neon", "Неоновая тема"),
        ("dark", "Тёмная тема"),
        ("light", "Светлая тема"),
        ("rose", "Тема сакуры"),
        ("unknown", "Неоновая тема"),
    ],
)
def test_email_verification_mailer_renders_theme_specific_html(
    monkeypatch, theme, expected_fragment
):
    """Проверяем, что EmailVerificationMailer строит HTML-письмо в палитре выбранной темы."""
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
            email_verification_expire_minutes=10,
        ),
    )
    html = EmailVerificationMailer()._build_html_message(
        code="123456",
        theme=EmailVerificationMailer()._normalize_theme(theme),
    )

    assert "123456" in html
    assert expected_fragment in html
