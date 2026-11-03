from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto.auth import (
    GoogleSignInCommand,
    LinkGoogleAccountCommand,
    UnlinkGoogleAccountCommand,
)
from backend.application.interface.services import GoogleIdentity
from backend.application.use_cases.auth.google.google_account import (
    GoogleSignInUseCase,
    LinkGoogleAccountUseCase,
    UnlinkGoogleAccountUseCase,
)
from backend.domain import User
from tests.support.fakes import FakeUnitOfWork

SUBJECT = "google-subject-1"
EMAIL = "someone@example.com"
ID_TOKEN = "id-token-value"


def _identity(**overrides: object) -> GoogleIdentity:
    """Собрать подтверждённую личность Google с возможностью переопределить поля."""
    fields = {"subject": SUBJECT, "email": EMAIL, "email_verified": True}
    fields.update(overrides)
    return GoogleIdentity(**fields)


def _user(*, user_id: int = 7, google_subject: str | None = None) -> User:
    """Собрать пользователя для проверок привязки."""
    return User(
        id=user_id,
        email=EMAIL,
        username="tester",
        password_hash="hashed",
        google_subject=google_subject,
    )


def _google_client(identity: GoogleIdentity | None) -> AsyncMock:
    """Собрать двойник порта Google, возвращающий заданную личность."""
    client = AsyncMock()
    client.verify_id_token.return_value = identity
    return client


def _sign_in(
    identity: GoogleIdentity | None,
    *,
    by_subject: User | None = None,
    by_email: User | None = None,
    added: User | None = None,
) -> tuple:
    """Собрать сценарий входа с двойниками порта, репозитория и паролей."""
    repository = AsyncMock()
    repository.get_by_google_subject.return_value = by_subject
    repository.get_by_email.return_value = by_email
    repository.add.return_value = added if added is not None else _user(user_id=42)
    repository.update.return_value = by_email
    password_service = AsyncMock()
    password_service.hash_password.return_value = "hashed-placeholder"
    use_case = GoogleSignInUseCase(
        FakeUnitOfWork(UserRepository=repository),
        _google_client(identity),
        password_service,
    )
    return use_case, repository, password_service


@pytest.mark.unit
class TestGoogleSignInUseCase:
    """Юнит-тесты входа через Google."""

    async def test_rejects_unverified_token(self):
        """Что тестируем: отказ при непроверенном ID-токене.
        Что передаём: порт возвращает None.
        Что ожидаем: отказ 401 без обращения к репозиторию.
        """
        use_case, repository, _passwords = _sign_in(None)

        result = await use_case.execute(GoogleSignInCommand(id_token=ID_TOKEN))

        assert result.ok is False
        assert result.status_code == 401
        repository.add.assert_not_awaited()

    async def test_returns_existing_user_by_subject(self):
        """Что тестируем: вход уже привязанного пользователя.
        Что передаём: поиск по google_subject находит пользователя.
        Что ожидаем: успех без создания и без обновления.
        """
        existing = _user(user_id=9, google_subject=SUBJECT)
        use_case, repository, _passwords = _sign_in(_identity(), by_subject=existing)

        result = await use_case.execute(GoogleSignInCommand(id_token=ID_TOKEN))

        assert result.ok is True
        assert result.data.id == 9
        repository.add.assert_not_awaited()
        repository.update.assert_not_awaited()

    async def test_links_existing_user_by_email(self):
        """Что тестируем: привязку Google к пользователю с той же почтой.
        Что передаём: по SUBJECT никого, по почте найден пользователь.
        Что ожидаем: вызов обновления с привязанным идентификатором.
        """
        by_email = _user(user_id=5)
        use_case, repository, _passwords = _sign_in(_identity(), by_email=by_email)

        result = await use_case.execute(GoogleSignInCommand(id_token=ID_TOKEN))

        assert result.ok is True
        assert by_email.google_subject == SUBJECT
        repository.update.assert_awaited_once_with(by_email)

    async def test_creates_new_user_with_generated_credentials(self):
        """Что тестируем: создание пользователя при отсутствии аккаунта.
        Что передаём: никого не нашли ни по SUBJECT, ни по почте.
        Что ожидаем: создан пользователь с именем из почты и привязкой Google.
        """
        use_case, repository, password_service = _sign_in(_identity(), added=_user(user_id=42))

        result = await use_case.execute(GoogleSignInCommand(id_token=ID_TOKEN))

        assert result.ok is True
        created = repository.add.await_args.args[0]
        assert created.username == "someone"
        assert created.google_subject == SUBJECT
        password_service.hash_password.assert_awaited_once()


def _link(
    identity: GoogleIdentity | None,
    *,
    holder: User | None = None,
    user: User | None = None,
) -> tuple:
    """Собрать сценарий привязки с двойниками порта и репозитория."""
    repository = AsyncMock()
    repository.get_by_google_subject.return_value = holder
    repository.get_by_id.return_value = user
    repository.update.return_value = user
    use_case = LinkGoogleAccountUseCase(
        FakeUnitOfWork(UserRepository=repository),
        _google_client(identity),
    )
    return use_case, repository


@pytest.mark.unit
class TestLinkGoogleAccountUseCase:
    """Юнит-тесты привязки аккаунта Google."""

    async def test_rejects_unverified_token(self):
        """Что тестируем: отказ при непроверенном токене.
        Что передаём: порт возвращает None.
        Что ожидаем: отказ 401.
        """
        use_case, _repository = _link(None)

        result = await use_case.execute(LinkGoogleAccountCommand(user_id=7, id_token=ID_TOKEN))

        assert result.ok is False
        assert result.status_code == 401

    async def test_rejects_subject_already_linked_to_other(self):
        """Что тестируем: конфликт занятой привязки.
        Что передаём: SUBJECT принадлежит другому пользователю.
        Что ожидаем: отказ 409 и никакого обновления.
        """
        use_case, repository = _link(_identity(), holder=_user(user_id=99))

        result = await use_case.execute(LinkGoogleAccountCommand(user_id=7, id_token=ID_TOKEN))

        assert result.ok is False
        assert result.status_code == 409
        repository.update.assert_not_awaited()

    async def test_links_when_subject_is_free(self):
        """Что тестируем: успешную привязку свободного аккаунта.
        Что передаём: SUBJECT свободен, пользователь сессии найден.
        Что ожидаем: успех и запись идентификатора через обновление.
        """
        user = _user(user_id=7)
        use_case, repository = _link(_identity(), user=user)

        result = await use_case.execute(LinkGoogleAccountCommand(user_id=7, id_token=ID_TOKEN))

        assert result.ok is True
        assert user.google_subject == SUBJECT
        repository.update.assert_awaited_once_with(user)


def _unlink(user: User | None) -> tuple:
    """Собрать сценарий отвязки с двойником репозитория."""
    repository = AsyncMock()
    repository.get_by_id.return_value = user
    repository.update.return_value = user
    use_case = UnlinkGoogleAccountUseCase(FakeUnitOfWork(UserRepository=repository))
    return use_case, repository


@pytest.mark.unit
class TestUnlinkGoogleAccountUseCase:
    """Юнит-тесты отвязки аккаунта Google."""

    async def test_returns_not_found_for_missing_user(self):
        """Что тестируем: отказ для несуществующего пользователя.
        Что передаём: репозиторий не нашёл пользователя.
        Что ожидаем: отказ 404.
        """
        use_case, _repository = _unlink(None)

        result = await use_case.execute(UnlinkGoogleAccountCommand(user_id=7))

        assert result.ok is False
        assert result.status_code == 404

    async def test_clears_google_subject(self):
        """Что тестируем: снятие привязки Google.
        Что передаём: пользователя с установленным SUBJECT.
        Что ожидаем: успех и очищенный идентификатор через обновление.
        """
        user = _user(user_id=7, google_subject=SUBJECT)
        use_case, repository = _unlink(user)

        result = await use_case.execute(UnlinkGoogleAccountCommand(user_id=7))

        assert result.ok is True
        assert user.google_subject is None
        repository.update.assert_awaited_once_with(user)
