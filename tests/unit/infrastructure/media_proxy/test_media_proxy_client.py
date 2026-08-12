from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.responses import JSONResponse, Response, StreamingResponse

from backend.infrastructure.media_proxy.media_proxy_client import MediaProxyClient


def _upstream_response(status_code=200, headers=None, text="", via_stream=False):
    headers = headers or {"Content-Type": "video/mp4"}
    obj = SimpleNamespace(
        status_code=status_code,
        headers=headers,
        text=text,
    )

    def raise_for_status():
        if obj.status_code >= 400:
            raise Exception(f"http {obj.status_code}")

    obj.raise_for_status = raise_for_status
    return obj


def _request(headers=None):
    return SimpleNamespace(headers=headers or {})


def _proxy_url_builder(url):
    return f"/proxy?url={url}"


class TestMediaProxyClient:
    async def test_blocks_disallowed_url(self):
        client = MediaProxyClient.__new__(MediaProxyClient)
        request = _request()
        response = await client.proxy(request, "https://evil.com/a.mp4", _proxy_url_builder)
        assert response.status_code == 403

    async def test_returns_json_error_on_http_error(self, monkeypatch):
        client = MediaProxyClient.__new__(MediaProxyClient)

        class _Client:
            async def get(self, *a, **k):
                import httpx

                raise httpx.ConnectError("network")

        client._client = _Client()
        response = await client.proxy(
            _request(), "https://cdn.libria.fun/a.mp4", _proxy_url_builder
        )
        assert isinstance(response, JSONResponse)
        assert response.status_code == 502

    async def test_hls_manifest_is_rewritten(self, monkeypatch):
        client = MediaProxyClient.__new__(MediaProxyClient)
        manifest = "#EXTM3U\nseg1.ts"
        upstream = _upstream_response(
            headers={"Content-Type": "application/vnd.apple.mpegurl"},
            text=manifest,
        )

        class _Client:
            async def get(self, url, headers=None):
                return upstream

        client._client = _Client()
        response = await client.proxy(
            _request(), "https://cdn.libria.fun/playlist.m3u8", _proxy_url_builder
        )
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert "/proxy?url=https://cdn.libria.fun/seg1.ts" in response.body.decode()

    async def test_media_is_streamed(self, monkeypatch):
        client = MediaProxyClient.__new__(MediaProxyClient)
        upstream = _upstream_response(headers={"Content-Type": "video/mp4"})

        class _Client:
            async def get(self, url, headers=None):
                return upstream

        class _Stream:
            def __init__(self):
                self.chunks = [b"data1", b"data2"]

            async def aiter_bytes(self, chunk_size):
                for chunk in self.chunks:
                    yield chunk

        client._client = _Client()
        client._stream = lambda url, headers: _Stream()
        response = await client.proxy(
            _request(), "https://cdn.libria.fun/video.mp4", _proxy_url_builder
        )
        assert isinstance(response, StreamingResponse)
        assert response.status_code == 200

    def test_passthrough_headers_pick_safe_ones(self):
        from backend.infrastructure.media_proxy.media_proxy_client import _passthrough_headers

        upstream = _upstream_response(
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": "100",
                "Set-Cookie": "evil=1",
            }
        )
        headers = _passthrough_headers(upstream)
        assert headers["Content-Type"] == "video/mp4"
        assert headers["Content-Length"] == "100"
        assert "Set-Cookie" not in headers