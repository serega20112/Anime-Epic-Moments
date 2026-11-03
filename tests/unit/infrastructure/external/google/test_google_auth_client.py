from __future__ import annotations

import httpx
import pytest

from backend.domain.clock import utc_now
from backend.infrastructure.external.google import GoogleAuthClient

CLIENT_ID = "app-client-id"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
VALID_EXP = int(utc_now().timestamp()) + 3600


def _client_with_claims(claims: object, *, status_code: int = 200) -> GoogleAuthClient:
    """Собрать клиент Google, отвечающий заданным телом tokeninfo."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=claims)

    return GoogleAuthClient(
        client_id=CLIENT_ID,
        tokeninfo_url=TOKENINFO_URL,
        transport=httpx.MockTransport(handler),
    )


def _valid_claims(**overrides: object) -> dict:
    """Собрать корректный набор заявлений с переопределением полей."""
    claims = {
        "aud": CLIENT_ID,
        "iss": "https://accounts.google.com",
        "sub": "subject-1",
        "email": "User@Example.com",
        "email_verified": "true",
        "exp": str(VALID_EXP),
        "name": "User",
        "picture": "https://example.com/a.png",
    }
    claims.update(overrides)
    return claims


@pytest.mark.unit
class TestGoogleAuthClient:
    """Юнит-тесты проверки ID-токена клиента Google."""

    async def test_returns_none_for_empty_client_id(self):
        """Что тестируем: выключенный вход без настроенного client_id.
        Что передаём: пустой client_id и корректный токен.
        Что ожидаем: None без сетевого обращения.
        """
        client = GoogleAuthClient(client_id="", tokeninfo_url=TOKENINFO_URL)

        identity = await client.verify_id_token("token")

        assert identity is None
        await client.aclose()

    async def test_returns_none_for_blank_token(self):
        """Что тестируем: отказ на пустом токене.
        Что передаём: токен из одних пробелов.
        Что ожидаем: None.
        """
        client = _client_with_claims(_valid_claims())

        identity = await client.verify_id_token("   ")

        assert identity is None
        await client.aclose()

    async def test_maps_verified_identity_and_normalizes_email(self):
        """Что тестируем: разбор подтверждённой личности и канонизацию почты.
        Что передаём: корректные заявления с заглавной почтой.
        Что ожидаем: личность с нижним регистром почты и флагом подтверждения.
        """
        client = _client_with_claims(_valid_claims())

        identity = await client.verify_id_token("token")

        assert identity is not None
        assert identity.subject == "subject-1"
        assert identity.email == "user@example.com"
        assert identity.email_verified is True
        assert identity.picture == "https://example.com/a.png"
        await client.aclose()

    @pytest.mark.parametrize(
        "overrides",
        [
            {"aud": "other-client"},
            {"iss": "https://evil.example"},
            {"exp": str(int(utc_now().timestamp()) - 10)},
            {"sub": ""},
            {"email": ""},
        ],
        ids=["wrong-aud", "wrong-iss", "expired", "no-subject", "no-email"],
    )
    async def test_rejects_untrusted_claims(self, overrides):
        """Что тестируем: отклонение недоверенных заявлений.
        Что передаём: испорченное поле корректного набора.
        Что ожидаем: None.
        """
        client = _client_with_claims(_valid_claims(**overrides))

        identity = await client.verify_id_token("token")

        assert identity is None
        await client.aclose()

    async def test_returns_none_when_tokeninfo_denies(self):
        """Что тестируем: отказ эндпоинта tokeninfo.
        Что передаём: HTTP-статус 400 от Google.
        Что ожидаем: None.
        """
        client = _client_with_claims(_valid_claims(), status_code=400)

        identity = await client.verify_id_token("token")

        assert identity is None
        await client.aclose()

    async def test_returns_none_on_malformed_body(self):
        """Что тестируем: разбор некорректного JSON ответа.
        Что передаём: валидный статус, но тело не-объект.
        Что ожидаем: None вместо исключения.
        """
        client = _client_with_claims([1, 2, 3])

        identity = await client.verify_id_token("token")

        assert identity is None
        await client.aclose()
