from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from backend.domain import User
from backend.infrastructure.repositories.user_repository import UserRepository
from backend.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.integration
class TestSqlAlchemyUnitOfWork:
    """Интеграционные тесты транзакционного поведения UnitOfWork."""

    async def test_commit_persists_pending_changes(self, async_db_session_factory):
        """Проверяем, что commit делает изменения видимыми для новых сессий."""
        async with async_db_session_factory() as session:
            repo = UserRepository(session)
            uow = SqlAlchemyUnitOfWork(session)
            created = await repo.add(
                User(
                    email="commit@example.com",
                    username="committer",
                    password_hash="hash-1",
                )
            )

            await uow.commit()

            assert created.id is not None

        async with async_db_session_factory() as fresh_session:
            loaded = await UserRepository(fresh_session).get_by_email("commit@example.com")
        assert loaded is not None
        assert loaded.username == "committer"

    async def test_rollback_discards_pending_changes(self, async_db_session_factory):
        """Проверяем, что rollback отбрасывает незакоммиченные изменения."""
        async with async_db_session_factory() as session:
            repo = UserRepository(session)
            uow = SqlAlchemyUnitOfWork(session)
            await repo.add(
                User(
                    email="rollback@example.com",
                    username="rolled-back",
                    password_hash="hash-1",
                )
            )

            await uow.rollback()

            loaded = await repo.get_by_email("rollback@example.com")
            assert loaded is None

        async with async_db_session_factory() as fresh_session:
            loaded = await UserRepository(fresh_session).get_by_email("rollback@example.com")
        assert loaded is None

    async def test_failed_commit_leaves_no_partial_rows(self, async_db_session_factory):
        """Проверяем, что ошибка коммита не оставляет частичных записей."""
        async with async_db_session_factory() as session:
            repo = UserRepository(session)
            uow = SqlAlchemyUnitOfWork(session)
            await repo.add(
                User(
                    email="unique@example.com",
                    username="first",
                    password_hash="hash-1",
                )
            )
            await uow.commit()

            with pytest.raises(IntegrityError):
                await repo.add(
                    User(
                        email="unique@example.com",
                        username="second",
                        password_hash="hash-2",
                    )
                )
                await uow.commit()
            await uow.rollback()

        async with async_db_session_factory() as fresh_session:
            repo = UserRepository(fresh_session)
            loaded = await repo.get_by_email("unique@example.com")
            assert loaded is not None
            assert loaded.username == "first"
