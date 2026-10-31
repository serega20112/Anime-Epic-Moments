"""HTTP-клиент медиапрокси: стримит медиа внешних хостов через приложение.

Владеет общим клиентом httpx, применяет список разрешённых хостов и
отдаёт медиа ответами Starlette, переписывая HLS-манифесты. На каждый
вызов делается один запрос к источнику: тело либо стримится клиенту,
либо, только для манифестов, буферизуется с ограничением размера.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx
from starlette import status
from starlette.responses import JSONResponse, Response, StreamingResponse

from backend.infrastructure.external.video.hls_proxy.hls_proxy import rewrite_hls_manifest
from backend.infrastructure.external.video.hls_proxy.url_policy import (
    browser_user_agent,
    is_allowed_media_url,
    is_hls_manifest,
)

logger = logging.getLogger("anime_epic_moments")

_MANIFEST_MEDIA_TYPE = "application/vnd.apple.mpegurl"
_OK_STATUS = int(status.HTTP_200_OK)
_REDIRECT_STATUS_FLOOR = int(status.HTTP_300_MULTIPLE_CHOICES)
_ERROR_STATUS_FLOOR = int(status.HTTP_400_BAD_REQUEST)
_STREAM_UNAVAILABLE_STATUS = int(status.HTTP_502_BAD_GATEWAY)
_FORBIDDEN_STATUS = int(status.HTTP_403_FORBIDDEN)
_CHUNK_SIZE = 64 * 1024
_MAX_MANIFEST_BYTES = 1024 * 1024
_MANIFEST_READ_CHUNK = 16 * 1024
_PASSTHROUGH_HEADERS = (
    "Content-Type",
    "Content-Length",
    "Accept-Ranges",
    "Content-Range",
)


class MediaProxyClient:
    """Стримит медиа с разрешённых хостов через приложение.

    Клиент нужно закрывать явно, чтобы освободить пул соединений.
    """

    def __init__(
        self,
        *,
        follow_redirects: bool = False,
        trust_env: bool = False,
        timeout: float = 30.0,
        upstream_proxy: str = "",
    ) -> None:
        """Создать клиент прокси без перехода по редиректам.

        Редиректы не отслеживаются, чтобы проверенный адрес не мог незаметно
        увести на непроверенный хост.
        """
        client_kwargs: dict = {
            "follow_redirects": follow_redirects,
            "trust_env": trust_env,
            "timeout": timeout,
        }
        normalized_proxy = str(upstream_proxy or "").strip()
        if normalized_proxy:
            client_kwargs["proxy"] = normalized_proxy
        self._client = httpx.AsyncClient(**client_kwargs)

    async def proxy(self, request, upstream_url: str, proxy_url_builder) -> Response:
        """Проксировать медиа по внешнему адресу."""
        if not await is_allowed_media_url(upstream_url):
            return Response(status_code=_FORBIDDEN_STATUS)
        request_headers = {
            "User-Agent": await browser_user_agent(request.headers.get("User-Agent"))
        }
        if request.headers.get("Range"):
            request_headers["Range"] = request.headers["Range"]

        upstream_request = self._client.build_request(
            "GET",
            upstream_url,
            headers=request_headers,
        )
        try:
            upstream_response = await self._client.send(upstream_request, stream=True)
        except httpx.HTTPError:
            logger.exception("watch_stream_proxy_failed url=%s", upstream_url)
            return JSONResponse(
                {"error": "stream_unavailable"}, status_code=_STREAM_UNAVAILABLE_STATUS
            )

        upstream_status = int(upstream_response.status_code or _OK_STATUS)
        if upstream_status >= _ERROR_STATUS_FLOOR or (
            _REDIRECT_STATUS_FLOOR <= upstream_status < _ERROR_STATUS_FLOOR
        ):
            await upstream_response.aclose()
            logger.warning(
                "watch_stream_upstream_error url=%s status=%s",
                upstream_url,
                upstream_status,
            )
            return JSONResponse(
                {"error": "stream_unavailable"}, status_code=_STREAM_UNAVAILABLE_STATUS
            )

        content_type = str(upstream_response.headers.get("Content-Type") or "").lower()
        if await is_hls_manifest(upstream_url=upstream_url, content_type=content_type):
            return await self._respond_manifest(upstream_response, upstream_url, proxy_url_builder)

        return StreamingResponse(
            self._stream_response(upstream_response),
            headers=await _passthrough_headers(upstream_response),
            status_code=upstream_status,
        )

    async def _respond_manifest(
        self,
        upstream_response,
        upstream_url: str,
        proxy_url_builder,
    ) -> Response:
        """Прочитать, переписать и закрыть ответ с HLS-манифестом."""
        content_length = str(upstream_response.headers.get("Content-Length") or "")
        if content_length.isdigit() and int(content_length) > _MAX_MANIFEST_BYTES:
            await upstream_response.aclose()
            logger.warning("watch_stream_manifest_too_large url=%s", upstream_url)
            return JSONResponse(
                {"error": "stream_unavailable"}, status_code=_STREAM_UNAVAILABLE_STATUS
            )
        try:
            manifest_bytes = await self._read_capped(upstream_response)
        except httpx.HTTPError:
            logger.exception("watch_stream_manifest_failed url=%s", upstream_url)
            return JSONResponse(
                {"error": "stream_unavailable"}, status_code=_STREAM_UNAVAILABLE_STATUS
            )
        if manifest_bytes is None:
            logger.warning("watch_stream_manifest_too_large url=%s", upstream_url)
            return JSONResponse(
                {"error": "stream_unavailable"}, status_code=_STREAM_UNAVAILABLE_STATUS
            )
        proxied_manifest = await rewrite_hls_manifest(
            manifest_bytes.decode("utf-8", errors="replace"),
            upstream_url,
            proxy_url_builder,
        )
        return Response(
            content=proxied_manifest,
            media_type=_MANIFEST_MEDIA_TYPE,
            status_code=int(upstream_response.status_code or _OK_STATUS),
        )

    async def _read_capped(self, upstream_response) -> bytes | None:
        """Прочитать тело ответа до предела размера манифеста."""
        chunks: list[bytes] = []
        total = 0
        try:
            async for chunk in upstream_response.aiter_bytes(chunk_size=_MANIFEST_READ_CHUNK):
                total += len(chunk)
                if total > _MAX_MANIFEST_BYTES:
                    return None
                chunks.append(chunk)
        finally:
            await upstream_response.aclose()
        return b"".join(chunks)

    async def _stream_response(self, upstream_response) -> AsyncIterator[bytes]:
        """Стримить тело ответа порциями и закрыть его после этого."""
        try:
            async for chunk in upstream_response.aiter_bytes(chunk_size=_CHUNK_SIZE):
                if chunk:
                    yield chunk
        finally:
            await upstream_response.aclose()

    async def aclose(self) -> None:
        """Закрыть клиент httpx и освободить пул соединений."""
        await self._client.aclose()


async def _passthrough_headers(upstream_response) -> dict[str, str]:
    """Скопировать безопасные заголовки ответа источника."""
    headers: dict[str, str] = {}
    for header_name in _PASSTHROUGH_HEADERS:
        value = upstream_response.headers.get(header_name)
        if value:
            headers[header_name] = value
    return headers
