"""Клиент проверки ID-токена Google через публичный эндпоинт tokeninfo."""

from __future__ import annotations

import logging

import httpx

from backend.application.interface.services import GoogleAuthClientInterface, GoogleIdentity
from backend.domain.clock import utc_now

GOOGLE_ISSUERS = frozenset({"https://accounts.google.com", "accounts.google.com"})
REQUEST_TIMEOUT_SECONDS = 10
logger = logging.getLogger("anime_epic_moments")


class GoogleAuthClient(GoogleAuthClientInterface):
    """Проверяет ID-токен Google, обращаясь к эндпоинту ``tokeninfo``."""

    def __init__(
        self,
        *,
        client_id: str,
        tokeninfo_url: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        """Создать клиент проверки токенов Google.

        Args:
            client_id: OAuth client ID нашего приложения, сверяемый с ``aud``.
            tokeninfo_url: Адрес эндпоинта проверки ID-токена Google.
            transport: Необязательный транспорт httpx для тестов.
        """
        self._client_id = client_id
        self._tokeninfo_url = tokeninfo_url
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, transport=transport)

    async def aclose(self) -> None:
        """Закрыть пул соединений клиента Google."""
        await self._client.aclose()

    async def verify_id_token(self, id_token: str) -> GoogleIdentity | None:
        """Проверить ID-токен и вернуть подтверждённую личность либо None.

        Токен считается действительным, только если ответы ``tokeninfo`` содержат
        наш ``aud``, известный ``iss`` и не истёкший ``exp``. Сетевые сбои и
        неверный токен трактуются одинаково — как отказ, а не как ошибка приложения.

        Args:
            id_token: JWT-токен, полученный клиентом от Google.

        Returns:
            GoogleIdentity | None: Подтверждённая личность либо None.
        """
        token = str(id_token or "").strip()
        if not token or not self._client_id:
            return None
        try:
            response = await self._client.get(self._tokeninfo_url, params={"id_token": token})
            if response.status_code != httpx.codes.OK:
                logger.info("google_tokeninfo_rejected status=%s", response.status_code)
                return None
            claims = response.json()
        except (httpx.HTTPError, ValueError):
            logger.info("google_tokeninfo_lookup_failed")
            return None
        return self._identity_from_claims(claims)

    def _identity_from_claims(self, claims: object) -> GoogleIdentity | None:
        """Извлечь и проверить заявления из ответа ``tokeninfo``.

        Args:
            claims: Разобранный JSON ответа Google.

        Returns:
            GoogleIdentity | None: Личность либо None при непройденной проверке.
        """
        if not isinstance(claims, dict):
            return None
        if str(claims.get("aud") or "") != self._client_id:
            return None
        if str(claims.get("iss") or "") not in GOOGLE_ISSUERS:
            return None
        subject = str(claims.get("sub") or "").strip()
        email = str(claims.get("email") or "").strip().lower()
        if not subject or not email:
            return None
        if not self._token_not_expired(claims.get("exp")):
            return None
        return GoogleIdentity(
            subject=subject,
            email=email,
            email_verified=str(claims.get("email_verified") or "").lower() in {"true", "1"},
            name=str(claims.get("name") or "").strip(),
            picture=str(claims.get("picture") or "").strip(),
        )

    @staticmethod
    def _token_not_expired(exp: object) -> bool:
        """Проверить, что срок действия токена ещё не истёк.

        Args:
            exp: Значение ``exp`` из заявлений — секунды эпохи либо None.

        Returns:
            bool: True, когда ``exp`` отсутствует либо ещё не прошёл.
        """
        try:
            expires_at = int(str(exp))
        except (TypeError, ValueError):
            return False
        return expires_at >= int(utc_now().timestamp())
