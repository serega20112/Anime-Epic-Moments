from __future__ import annotations

import httpx
from starlette.responses import JSONResponse, Response, StreamingResponse

from backend.infrastructure.external.video.hls_proxy import MediaProxyClient


def _streamed_upstream_response(status_code=200, headers=None, body_chunks=None):
    headers = headers or {"Content-Type": "video/mp4"}
    chunks = body_chunks if body_chunks is not None else [b"data1", b"data2"]
    closed = {"value": False}

    class _Response:
        def __init__(self):
            self.status_code = status_code
            self.headers = headers

        async def aiter_bytes(self, chunk_size):
            for chunk in chunks:
                yield chunk

        async def aclose(self):
            closed["value"] = True

    return _Response(), closed


def _request(headers=None):
    class _Request:
        def __init__(self):
            self.headers = headers or {}

    return _Request()


def _proxy_url_builder(url):
    return f"/proxy?url={url}"


def _client_with(response_obj):
    client = MediaProxyClient.__new__(MediaProxyClient)

    class _HttpxClient:
        def build_request(self, method, url, headers=None):
            return httpx.Request(method, url, headers=headers or {})

        async def send(self, request, stream=False):
            return response_obj

    client._client = _HttpxClient()
    return client


class TestMediaProxyClient:
    async def test_blocks_disallowed_url(self):
        client = MediaProxyClient.__new__(MediaProxyClient)
        request = _request()
        response = await client.proxy(request, "https://evil.com/a.mp4", _proxy_url_builder)
        assert response.status_code == 403

    async def test_returns_json_error_on_http_error(self, monkeypatch):
        client = MediaProxyClient.__new__(MediaProxyClient)

        class _Client:
            def build_request(self, method, url, headers=None):
                return httpx.Request(method, url, headers=headers or {})

            async def send(self, request, stream=False):
                raise httpx.ConnectError("network")

        client._client = _Client()
        response = await client.proxy(
            _request(), "https://cdn.libria.fun/a.mp4", _proxy_url_builder
        )
        assert isinstance(response, JSONResponse)
        assert response.status_code == 502

    async def test_upstream_error_status_returns_502_and_closes(self):
        upstream, closed = _streamed_upstream_response(status_code=404)
        client = _client_with(upstream)

        response = await client.proxy(
            _request(), "https://cdn.libria.fun/a.mp4", _proxy_url_builder
        )

        assert isinstance(response, JSONResponse)
        assert response.status_code == 502
        assert closed["value"] is True

    async def test_hls_manifest_is_rewritten(self):
        manifest = "#EXTM3U\nseg1.ts"
        upstream, closed = _streamed_upstream_response(
            headers={"Content-Type": "application/vnd.apple.mpegurl"},
            body_chunks=[manifest.encode("utf-8")],
        )
        client = _client_with(upstream)

        response = await client.proxy(
            _request(), "https://cdn.libria.fun/playlist.m3u8", _proxy_url_builder
        )

        assert isinstance(response, Response)
        assert response.status_code == 200
        assert "/proxy?url=https://cdn.libria.fun/seg1.ts" in response.body.decode()
        assert closed["value"] is True

    async def test_oversized_manifest_is_rejected(self):
        big_chunk = b"x" * (1024 * 1024 + 1)
        upstream, closed = _streamed_upstream_response(
            headers={"Content-Type": "application/vnd.apple.mpegurl"},
            body_chunks=[big_chunk],
        )
        client = _client_with(upstream)

        response = await client.proxy(
            _request(), "https://cdn.libria.fun/playlist.m3u8", _proxy_url_builder
        )

        assert isinstance(response, JSONResponse)
        assert response.status_code == 502
        assert closed["value"] is True

    async def test_media_is_streamed_from_single_upstream_response(self):
        upstream, closed = _streamed_upstream_response(headers={"Content-Type": "video/mp4"})
        client = _client_with(upstream)

        response = await client.proxy(
            _request(), "https://cdn.libria.fun/video.mp4", _proxy_url_builder
        )

        assert isinstance(response, StreamingResponse)
        assert response.status_code == 200

        received = b""
        async for chunk in response.body_iterator:
            received += chunk

        assert received == b"data1data2"
        assert closed["value"] is True

    async def test_passthrough_headers_pick_safe_ones(self):
        from backend.infrastructure.external.video.hls_proxy.media_proxy_client import (
            _passthrough_headers,
        )

        upstream, _closed = _streamed_upstream_response(
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": "100",
                "Set-Cookie": "evil=1",
            }
        )
        headers = await _passthrough_headers(upstream)
        assert headers["Content-Type"] == "video/mp4"
        assert headers["Content-Length"] == "100"
        assert "Set-Cookie" not in headers
