"""Интеграционные тесты репозитория тикетов поддержки.

Тикет ссылается на пользователя внешним ключом, поэтому тесты создают реальную запись
`users`: на PostgreSQL висячий `user_id` отклоняется, а sqlite вне контейнеров внешних
ключей не проверяет.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from backend.domain import User
from backend.domain.entities.support.support_ticket import SupportTicket
from backend.infrastructure.database.repositories.support_repository import SupportRepository
from backend.infrastructure.database.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestSupportRepository:
    async def test_adds_and_reads_ticket(self, async_db_session):
        """Тикет авторизованного пользователя сохраняется со статусами по умолчанию."""
        user = await UserRepository(async_db_session).add(
            User(email="support@example.com", username="supportor", password_hash="hash")
        )
        repo = SupportRepository(async_db_session)
        ticket = SupportTicket(
            email="a@b.com",
            username="tester",
            subject="Help",
            message="Broken page",
            channel="email",
            user_id=user.id,
            page_url="https://x.com",
        )

        saved = await repo.add(ticket)

        assert saved.id is not None
        assert saved.email == "a@b.com"
        assert saved.status == "open"
        assert saved.delivery_status == "pending"
        assert saved.user_id == user.id

    async def test_ticket_without_user_is_accepted(self, async_db_session):
        """Гостевой тикет сохраняется: `user_id` допустим как NULL."""
        repo = SupportRepository(async_db_session)

        saved = await repo.add(
            SupportTicket(
                email="guest@example.com",
                username="guest",
                subject="S",
                message="M",
                channel="email",
            )
        )

        assert saved.id is not None
        assert saved.user_id is None

    async def test_ticket_with_unknown_user_violates_foreign_key(self, async_db_session):
        """База обязана отклонить тикет на несуществующего пользователя.

        Проверка имеет смысл только на PostgreSQL: sqlite не включает `PRAGMA foreign_keys`,
        поэтому на нём ограничение молча проходит и тест пропускается.
        """
        if async_db_session.bind.dialect.name != "postgresql":
            pytest.skip("внешние ключи проверяются только на PostgreSQL")

        repo = SupportRepository(async_db_session)

        with pytest.raises(IntegrityError):
            await repo.add(
                SupportTicket(
                    email="ghost@example.com",
                    username="ghost",
                    subject="S",
                    message="M",
                    channel="email",
                    user_id=999_999,
                )
            )

    async def test_update_existing_ticket(self, async_db_session):
        """Статусы тикета обновляются по сохранённому идентификатору."""
        repo = SupportRepository(async_db_session)
        ticket = SupportTicket(
            email="a@b.com",
            username="tester",
            subject="S",
            message="M",
            channel="telegram",
        )
        saved = await repo.add(ticket)

        saved.status = "resolved"
        saved.delivery_status = "sent"
        updated = await repo.update(saved)

        assert updated.id == saved.id
        assert updated.status == "resolved"
        assert updated.delivery_status == "sent"

    async def test_update_missing_ticket_raises(self, async_db_session):
        """Обновление несуществующего тикета превращается в ошибку домена."""
        repo = SupportRepository(async_db_session)
        ticket = SupportTicket(
            id=999,
            email="a@b.com",
            username="t",
            subject="S",
            message="M",
        )
        with pytest.raises(ValueError):
            await repo.update(ticket)
