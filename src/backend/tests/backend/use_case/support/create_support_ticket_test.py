from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.backend.infrastructure.models.sqlalchemy_models import SupportTicketModel
from src.backend.infrastructure.repositories.support_repository import SupportRepository
from src.backend.use_case.support.create_support_ticket import (
    CreateSupportTicketUseCase,
    InvalidSupportTicketError,
)


def test_create_support_ticket_saves_ticket_and_marks_it_sent(db_session):
    """Проверяем, что Telegram-тикет идет только в Telegram notifier."""
    telegram_notifier = Mock()
    email_mailer = Mock()
    telegram_notifier.send_ticket_created.return_value = 1
    use_case = CreateSupportTicketUseCase(
        support_repo=SupportRepository(db_session),
        telegram_notifier=telegram_notifier,
        email_mailer=email_mailer,
    )

    ticket = use_case.execute(
        user_id=7,
        email="user@example.com",
        username="tester",
        subject="Проблема с плеером",
        message="На 12 серии зависает воспроизведение после 10 минуты.",
        channel="telegram",
        page_url="https://example.com/watch/42",
    )

    db_ticket = db_session.query(SupportTicketModel).filter_by(id=ticket.id).first()

    assert ticket.id is not None
    assert ticket.delivery_status == "sent"
    assert ticket.delivery_error is None
    assert db_ticket is not None
    assert db_ticket.channel == "telegram"
    assert db_ticket.delivery_status == "sent"
    telegram_notifier.send_ticket_created.assert_called_once()
    email_mailer.send_ticket_created.assert_not_called()


def test_create_support_ticket_sends_email_ticket_without_touching_telegram(db_session):
    """Проверяем, что email-тикет идет только в email mailer."""
    telegram_notifier = Mock()
    email_mailer = Mock()
    email_mailer.send_ticket_created.return_value = 1
    use_case = CreateSupportTicketUseCase(
        support_repo=SupportRepository(db_session),
        telegram_notifier=telegram_notifier,
        email_mailer=email_mailer,
    )

    ticket = use_case.execute(
        email="guest@example.com",
        username="guest-user",
        subject="Сломан поиск",
        message="Поиск возвращает пустой список даже на Naruto.",
        channel="email",
        page_url="/anime/search?title=naruto",
    )

    db_ticket = db_session.query(SupportTicketModel).filter_by(id=ticket.id).first()

    assert ticket.id is not None
    assert ticket.channel == "email"
    assert ticket.delivery_status == "sent"
    assert db_ticket is not None
    assert db_ticket.channel == "email"
    assert db_ticket.delivery_status == "sent"
    telegram_notifier.send_ticket_created.assert_not_called()
    email_mailer.send_ticket_created.assert_called_once()


def test_create_support_ticket_marks_ticket_failed_when_selected_channel_is_down(db_session):
    """Проверяем, что тикет не теряется, если выбранный канал доставки недоступен."""
    telegram_notifier = Mock()
    email_mailer = Mock()
    telegram_notifier.send_ticket_created.side_effect = RuntimeError("telegram down")
    use_case = CreateSupportTicketUseCase(
        support_repo=SupportRepository(db_session),
        telegram_notifier=telegram_notifier,
        email_mailer=email_mailer,
    )

    ticket = use_case.execute(
        email="guest@example.com",
        username="guest-user",
        subject="Сломан поиск",
        message="Поиск возвращает пустой список даже на Naruto.",
        channel="telegram",
        page_url="/anime/search?title=naruto",
    )

    db_ticket = db_session.query(SupportTicketModel).filter_by(id=ticket.id).first()

    assert ticket.id is not None
    assert ticket.channel == "telegram"
    assert ticket.delivery_status == "failed"
    assert "telegram down" in (ticket.delivery_error or "")
    assert db_ticket is not None
    assert db_ticket.channel == "telegram"
    assert db_ticket.delivery_status == "failed"
    assert "telegram down" in (db_ticket.delivery_error or "")
    email_mailer.send_ticket_created.assert_not_called()


def test_create_support_ticket_rejects_unknown_channel(db_session):
    """Проверяем, что use case не принимает неизвестный канал доставки."""
    telegram_notifier = Mock()
    email_mailer = Mock()
    use_case = CreateSupportTicketUseCase(
        support_repo=SupportRepository(db_session),
        telegram_notifier=telegram_notifier,
        email_mailer=email_mailer,
    )

    with pytest.raises(InvalidSupportTicketError):
        use_case.execute(
            email="user@example.com",
            username="tester",
            subject="Проблема с уведомлением",
            message="Пробую отправить тикет в несуществующий канал доставки.",
            channel="discord",
        )

    assert db_session.query(SupportTicketModel).count() == 0


@pytest.mark.parametrize(
    ("email", "username", "subject", "message"),
    [
        ("bad-email", "tester", "Тема", "Нормальное описание проблемы"),
        ("user@example.com", "", "Тема", "Нормальное описание проблемы"),
        ("user@example.com", "tester", "No", "Нормальное описание проблемы"),
        ("user@example.com", "tester", "Тема", "short"),
    ],
)
def test_create_support_ticket_rejects_invalid_payload(
    db_session,
    email,
    username,
    subject,
    message,
):
    """Проверяем базовую валидацию payload перед сохранением тикета."""
    telegram_notifier = Mock()
    email_mailer = Mock()
    use_case = CreateSupportTicketUseCase(
        support_repo=SupportRepository(db_session),
        telegram_notifier=telegram_notifier,
        email_mailer=email_mailer,
    )

    with pytest.raises(InvalidSupportTicketError):
        use_case.execute(
            email=email,
            username=username,
            subject=subject,
            message=message,
            channel="telegram",
        )

    assert db_session.query(SupportTicketModel).count() == 0
