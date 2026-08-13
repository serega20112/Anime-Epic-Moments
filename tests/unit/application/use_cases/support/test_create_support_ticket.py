from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from backend.application.dto import CreateSupportTicketCommand
from backend.application.use_cases.support.create_support_ticket import (
    CreateSupportTicketUseCase,
    InvalidSupportTicketError,
)


@pytest.mark.unit
class TestCreateSupportTicketUseCase:
    """Юнит-тесты сценария создания тикета поддержки."""

    def _use_case(self, repo=None, telegram=None, email=None):
        support_repo = repo or AsyncMock()
        return CreateSupportTicketUseCase(
            support_repo=support_repo,
            telegram_notifier=telegram or AsyncMock(),
            email_mailer=email or AsyncMock(),
            unit_of_work=AsyncMock(),
        ), support_repo

    @pytest.mark.parametrize("channel", ["telegram", "email"])
    async def test_saves_ticket_and_sends_only_to_selected_channel(self, channel):
        """Что тестируем: доставку тикета строго через выбранный канал.
        Что передаём: команду с channel и замоканный репозиторий.
        Что ожидаем: тикет сохранен, помечен доставленным, только нужный канал вызван.
        """
        telegram = AsyncMock()
        email_mailer = AsyncMock()
        repo = AsyncMock()
        repo.add.side_effect = lambda ticket: self._with_id(ticket, 7)
        repo.update.side_effect = lambda ticket: ticket
        use_case = CreateSupportTicketUseCase(repo, telegram, email_mailer, AsyncMock())

        result = await use_case.execute(
            CreateSupportTicketCommand(
                user_id=7,
                email="user@example.com",
                username="tester",
                subject="Проблема с плеером",
                message="На 12 серии зависает воспроизведение после 10 минуты.",
                channel=channel,
                page_url="https://example.com/watch/42",
            )
        )

        assert result.ok is True
        assert result.status_code == 200
        assert result.data.id == 7
        assert result.data.channel == channel
        assert result.data.delivery_status == "sent"
        assert result.data.delivery_error is None
        repo.add.assert_awaited_once()
        repo.update.assert_awaited_once()
        if channel == "telegram":
            telegram.send_ticket_created.assert_awaited_once()
            email_mailer.send_ticket_created.assert_not_awaited()
        else:
            email_mailer.send_ticket_created.assert_awaited_once()
            telegram.send_ticket_created.assert_not_awaited()

    async def test_marks_ticket_failed_when_selected_channel_is_down(self):
        """Что тестируем: сохранение тикета при недоступном канале доставки.
        Что передаём: send_ticket_created бросает RuntimeError.
        Что ожидаем: тикет помечается failed с сообщением, результат ok=True, service_unavailable=True.
        """
        telegram = AsyncMock()
        telegram.send_ticket_created.side_effect = RuntimeError("telegram down")
        email_mailer = AsyncMock()
        repo = AsyncMock()
        repo.add.side_effect = lambda ticket: self._with_id(ticket, 8)
        repo.update.side_effect = lambda ticket: ticket
        use_case = CreateSupportTicketUseCase(repo, telegram, email_mailer, AsyncMock())

        result = await use_case.execute(
            CreateSupportTicketCommand(
                user_id=None,
                email="guest@example.com",
                username="guest-user",
                subject="Сломан поиск",
                message="Поиск возвращает пустой список даже на Naruto.",
                channel="telegram",
                page_url="/anime/search?title=naruto",
            )
        )

        assert result.ok is True
        assert result.service_unavailable is True
        assert result.data.channel == "telegram"
        assert result.data.delivery_status == "failed"
        assert "telegram down" in result.data.delivery_error
        email_mailer.send_ticket_created.assert_not_awaited()
        repo.update.assert_awaited_once()

    @pytest.mark.parametrize(
        ("subject", "expected_message"),
        [("telegram", "Telegram"), ("email", "email")],
    )
    async def test_delivers_failure_when_unknown_channel_does_not_reach_repo(
            self, subject, expected_message
    ):
        """Что тестируем: отказ при неизвестном канале доставки без сохранения.
        Что передаём: команду с channel=discord.
        Что ожидаем: результат failure со статусом 400, repo.add не вызывается.
        """
        repo = AsyncMock()
        use_case = self._use_case(repo=repo)[0]

        result = await use_case.execute(
            CreateSupportTicketCommand(
                user_id=None,
                email="user@example.com",
                username="tester",
                subject=subject,
                message="Пробую отправить тикет в несуществующий канал доставки.",
                channel="discord",
            )
        )

        assert result.ok is False
        assert result.status_code == 400
        repo.add.assert_not_awaited()

    @pytest.mark.parametrize(
        ("email", "username", "subject", "message"),
        [
            ("bad-email", "tester", "Тема", "Нормальное описание проблемы"),
            ("user@example.com", "", "Тема", "Нормальное описание проблемы"),
            ("user@example.com", "tester", "No", "Нормальное описание проблемы"),
            ("user@example.com", "tester", "Тема", "short"),
        ],
    )
    async def test_rejects_invalid_payload(self, email, username, subject, message):
        """Что тестируем: базовую валидацию payload перед сохранением.
        Что передаём: комбинации невалидных полей.
        Что ожидаем: результат failure со статусом 400 и repo не вызывается.
        """
        repo = AsyncMock()
        use_case = self._use_case(repo=repo)[0]

        result = await use_case.execute(
            CreateSupportTicketCommand(
                user_id=None,
                email=email,
                username=username,
                subject=subject,
                message=message,
                channel="telegram",
            )
        )

        assert result.ok is False
        assert result.status_code == 400
        repo.add.assert_not_awaited()

    def _with_id(self, ticket, ticket_id):
        ticket.id = ticket_id
        return ticket