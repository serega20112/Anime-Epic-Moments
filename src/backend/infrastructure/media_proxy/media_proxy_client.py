"""HTTP media streaming client that proxies upstream media through the app.

Owns the shared httpx client, applies the host allowlist, and streams media
responses (with HLS manifest orchestration) as Starlette responses.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx
from starlette.responses import JSONResponse, Response, StreamingResponse

from backend.infrastructure.media_proxy.hls_proxy import rewrite_hls_manifest
from backend.infrastructure.media_proxy.url_policy import (
    browser_user_agent,
    is_allowed_media_url,
    is_hls_manifest,
)

logger = logging.getLogger("anime_epic_moments")

_MANIFEST_MEDIA_TYPE = "application/vnd.apple.mpegurl"
_CHUNK_SIZE = 64 * 1024
_PASSTHROUGH_HEADERS = (
    "Content-Type",
    "Content-Length",
    "Accept-Ranges",
    "Content-Range",
)


class MediaProxyClient:
    """Streams media from allowed upstream hosts through the app.

    The client must be closed explicitly to release its connection pool.
    """

    def __init__(
        self,
        *,
        follow_redirects: bool = False,
        trust_env: bool = False,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the proxy client.

        Redirects are not followed so a vetted URL cannot silently bounce to
        an unvetted host (SSRF hardening).

        Args:
            follow_redirects: Whether to follow upstream redirects.
            trust_env: Whether to use environment proxies.
            timeout: Request timeout in seconds.
        """
        self._client = httpx.AsyncClient(
            follow_redirects=follow_redirects,
            trust_env=trust_env,
            timeout=timeout,
        )

    async def proxy(self, request, upstream_url: str, proxy_url_builder) -> Response:
        """Proxy an upstream media URL.

        Args:
            request: Incoming HTTP request (for Range/User-Agent passthrough).
            upstream_url: Allowed upstream media URL.
            proxy_url_builder: Callable mapping an absolute media URL to its proxy URL.

        Returns:
            Response: Proxied media response or an error response.
        """
        if not is_allowed_media_url(upstream_url):
            return Response(status_code=403)
        request_headers = {"User-Agent": browser_user_agent(request.headers.get("User-Agent"))}
        if request.headers.get("Range"):
            request_headers["Range"] = request.headers["Range"]
        try:
            upstream_response = await self._client.get(
                upstream_url,
                headers=request_headers,
            )
            upstream_response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("watch_stream_proxy_failed url=%s", upstream_url)
            return JSONResponse({"error": "stream_unavailable"}, status_code=502)

        upstream_status = int(upstream_response.status_code or 200)
        if 300 <= upstream_status < 400:
            logger.warning("watch_stream_redirect_blocked url=%s", upstream_url)
            return JSONResponse({"error": "stream_unavailable"}, status_code=502)

        content_type = str(upstream_response.headers.get("Content-Type") or "").lower()
        if is_hls_manifest(upstream_url=upstream_url, content_type=content_type):
            proxied_manifest = rewrite_hls_manifest(
                upstream_response.text,
                upstream_url,
                proxy_url_builder,
            )
            return Response(
                content=proxied_manifest,
                media_type=_MANIFEST_MEDIA_TYPE,
                status_code=upstream_status,
            )

        return StreamingResponse(
            self._stream(upstream_url, request_headers),
            headers=_passthrough_headers(upstream_response),
            status_code=upstream_status,
        )

    async def _stream(
        self, upstream_url: str, request_headers: dict[str, str]
    ) -> AsyncIterator[bytes]:
        """Stream upstream body in chunks.

        Args:
            upstream_url: Upstream media URL.
            request_headers: Request headers forwarded upstream.

        Yields:
            bytes: Upstream body chunks.
        """
        async with self._client.stream(
            "GET",
            upstream_url,
            headers=request_headers,
        ) as stream_response:
            async for chunk in stream_response.aiter_bytes(chunk_size=_CHUNK_SIZE):
                if chunk:
                    yield chunk

    async def aclose(self) -> None:
        """Close the underlying httpx client and release its connection pool."""
        await self._client.aclose()


def _passthrough_headers(upstream_response) -> dict[str, str]:
    """Copy safe response headers from the upstream response.

    Args:
        upstream_response: Upstream httpx response.

    Returns:
        dict[str, str]: Selected response headers.
    """
    headers: dict[str, str] = {}
    for header_name in _PASSTHROUGH_HEADERS:
        value = upstream_response.headers.get(header_name)
        if value:
            headers[header_name] = value
    return headers
