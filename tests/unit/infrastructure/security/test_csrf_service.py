from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.infrastructure.security.csrf_service import CSRFService, CSRFToken


def _expired_token() -> CSRFToken:
    """Создать токен, у которого срок действия уже истёк.

    Returns:
        CSRFToken: Токен, истёкший минуту назад.
    """
    return CSRFToken(value="expired-value", expires_at=datetime.now(UTC) - timedelta(minutes=1))


class TestCSRFService:
    """Юнит-тесты генерации и проверки CSRF-токенов."""

    @pytest.mark.unit
    def test_generate_token_returns_value_and_expiry(self):
        """Что тестируем: метод generate_token.

        Что передаём: ничего, сервис не зависит от запроса.
        Что ожидаем: токен со случайным значением и будущим моментом истечения.
        """
        service = CSRFService()

        token = service.generate_token()

        assert token.value
        assert token.expires_at > datetime.now(UTC)
        assert not token.is_expired()

    @pytest.mark.unit
    def test_session_roundtrip_preserves_token(self):
        """Что тестируем: пару to_session/from_session.

        Что передаём: токен, сериализованный для хранения в сессии.
        Что ожидаем: восстановленный токен сохраняет значение и момент истечения.
        """
        service = CSRFService()
        token = service.generate_token()

        restored = CSRFToken.from_session(token.to_session())

        assert restored is not None
        assert restored.value == token.value
        assert restored.expires_at == token.expires_at

    @pytest.mark.unit
    def test_from_session_accepts_legacy_plain_string(self):
        """Что тестируем: чтение токена, сохранённого до появления срока действия.

        Что передаём: голоую строку вместо словаря.
        Что ожидаем: токен восстановлен как бессрочный, чтобы старые сессии не падали.
        """
        token = CSRFToken.from_session("legacy-token")

        assert token is not None
        assert token.value == "legacy-token"
        assert not token.is_expired()

    @pytest.mark.unit
    @pytest.mark.parametrize("raw", [None, "", 42, {"value": "x"}, {"expires_at": "не дата"}])
    def test_from_session_rejects_damaged_data(self, raw):
        """Что тестируем: чтение повреждённых данных сессии.

        Что передаём: отсутствие токена, неверный тип и incomplete-словари.
        Что ожидаем: None вместо исключения, чтобы мидлвар мог выдать новый токен.
        """
        assert CSRFToken.from_session(raw) is None

    @pytest.mark.unit
    def test_is_valid_without_stored_token(self):
        """Что тестируем: проверку токена, когда в сессии его нет.

        Что передаём: None вместо хранящегося токена.
        Что ожидаем: False, значения сравнивать не с чем.
        """
        service = CSRFService()

        assert service.is_valid(None, "abc") is False

    @pytest.mark.unit
    def test_is_valid_rejects_empty_submission(self):
        """Что тестируем: проверку формы без поля csrf_token.

        Что передаём: действующий токен и пустое присланное значение.
        Что ожидаем: False.
        """
        service = CSRFService()
        token = service.generate_token()

        assert service.is_valid(token, None) is False
        assert service.is_valid(token, "") is False

    @pytest.mark.unit
    def test_is_valid_rejects_mismatch(self):
        """Что тестируем: проверку присланного значения, не совпадающего с токеном.

        Что передаём: валидный токен и другое значение от клиента.
        Что ожидаем: False.
        """
        service = CSRFService()
        token = service.generate_token()

        assert service.is_valid(token, "wrong") is False

    @pytest.mark.unit
    def test_is_valid_accepts_matching_token(self):
        """Что тестируем: успешную проверку CSRF-токена.

        Что передаём: токен из сессии и ровно то же значение от клиента.
        Что ожидаем: True.
        """
        service = CSRFService()
        token = service.generate_token()

        assert service.is_valid(token, token.value) is True

    @pytest.mark.unit
    def test_is_valid_rejects_expired_token(self):
        """Что тестируем: проверку истёкшего токена.

        Что передаём: токен с моментом истечения в прошлом и то же значение.
        Что ожидаем: False, срок действия важнее совпадения значений.
        """
        service = CSRFService()

        assert service.is_valid(_expired_token(), "expired-value") is False

    @pytest.mark.unit
    def test_expire_minutes_are_honoured(self):
        """Что тестируем: параметр token_expire_minutes.

        Что передаём: сервис с нулевым временем жизни токена.
        Что ожидаем: только что созданный токен уже недействителен.
        """
        service = CSRFService(token_expire_minutes=0)

        token = service.generate_token()

        assert token.is_expired() is True
        assert service.is_valid(token, token.value) is False

    @pytest.mark.unit
    def test_tokens_are_unique(self):
        """Что тестируем: случайность генерируемых токенов.

        Что передаём: два вызова generate_token подряд.
        Что ожидаем: значения различаются.
        """
        service = CSRFService()

        assert service.generate_token().value != service.generate_token().value
