"""Подбор рабочего токена Kodik с backoff между проверками.

Kodik не сообщает заранее, какой из токенов жив: единственный способ — лёгкий
пробный поиск. Проверять всех кандидатов на каждый запрос слишком дорого,
поэтому удачный токен запоминается, а после полного провала проверки
откладываются на ``_PROBE_BACKOFF_SECONDS``.
"""

from __future__ import annotations

import time

import httpx

from backend.infrastructure.external.video.kodik.token_store import KodikTokenStore

PROBE_BACKOFF_SECONDS = 300.0


class KodikTokenManager:
    """Хранит подтверждённый токен Kodik и решает, когда проверять заново."""

    def __init__(
        self,
        session: httpx.AsyncClient,
        api_url: str,
        token_store: KodikTokenStore,
        configured_token: str,
    ) -> None:
        """Создаёт менеджер токенов.

        Args:
            session: HTTP-клиент, которым пользуется провайдер.
            api_url: Базовый URL API Kodik без завершающего слеша.
            token_store: Хранилище кандидатов из конфига и файла.
            configured_token: Токен из настроек, если он задан.
        """
        self._session = session
        self._api_url = api_url
        self._token_store = token_store
        self._configured_token = configured_token
        self.working_token: str | None = None
        self._probe_retry_at: float = 0.0

    async def is_enabled(self) -> bool:
        """Проверяет, есть ли хоть один кандидат для запросов.

        Returns:
            bool: True, если задан токен из конфига или найден файл-хранилище.
        """
        return bool(self._configured_token) or bool(await self._token_store.candidates())

    async def resolve(self) -> str | None:
        """Возвращает подтверждённый токен или None в режиме backoff.

        Returns:
            str | None: Рабочий токен либо None, если проверки отложены или
            все кандидаты провалились.
        """
        if self.working_token:
            return self.working_token
        if time.monotonic() < self._probe_retry_at:
            return None
        for token in await self._token_store.candidates():
            if await self._probe(token):
                self.working_token = token
                return token
        self._probe_retry_at = time.monotonic() + PROBE_BACKOFF_SECONDS
        return None

    async def _probe(self, token: str) -> bool:
        """Проверяет токен одним лёгким запросом к поиску.

        Args:
            token: Проверяемый токен.

        Returns:
            bool: True, если API принял токен.
        """
        probe_params: dict[str, str | int] = {
            "token": token,
            "title": "test",
            "episode": 1,
            "limit": 1,
        }
        try:
            response = await self._session.get(
                f"{self._api_url}/search",
                params=probe_params,
            )
            status_code = getattr(response, "status_code", 200)
            if status_code != 200:
                return False
            payload = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            return False
        return not await KodikTokenStore.token_looks_invalid(payload)
