from __future__ import annotations

import pytest

from backend.infrastructure.media_proxy.url_policy import (
    ALLOWED_MEDIA_HOST_SUFFIXES,
    browser_user_agent,
    is_allowed_media_url,
    is_hls_manifest,
)


class TestAllowedMediaUrl:
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://s1.libria.fun/a.mp4", True),
            ("https://libria.fun/x", True),
            ("https://video.kodikplayer.com/y.m3u8", True),
            ("http://anilibria.tv/z", True),
            ("https://cdn.anilibria.host/hls/a.m3u8", True),
            ("https://vkvideo.ru/video/123", True),
            ("https://ok.ru/video/123", True),
            ("https://www.youtube.com/watch?v=abc", True),
            ("https://evil.com/a.mp4", False),
            ("ftp://libria.fun/a", False),
            ("not-a-url", False),
            ("", False),
            (None, False),
        ],
    )
    def test_allowlist(self, url, expected):
        assert is_allowed_media_url(url) is expected


def test_allowed_host_suffixes_non_empty():
    assert len(ALLOWED_MEDIA_HOST_SUFFIXES) > 0


class TestIsHlsManifest:
    @pytest.mark.parametrize(
        "url,content_type,expected",
        [
            ("https://x.com/playlist.m3u8", "text/plain", True),
            ("https://x.com/master.M3U8", "text/plain", True),
            ("https://x.com/video.mp4", "application/vnd.apple.mpegurl", True),
            ("https://x.com/video.mp4", "video/mp4", False),
        ],
    )
    def test_detection(self, url, content_type, expected):
        assert is_hls_manifest(url, content_type) is expected


class TestBrowserUserAgent:
    def test_uses_provided(self):
        assert browser_user_agent("Firefox/1.0") == "Firefox/1.0"

    def test_strips_whitespace(self):
        assert browser_user_agent("  Chrome/1.0  ") == "Chrome/1.0"

    def test_falls_back_to_default(self):
        assert browser_user_agent(None) == "Mozilla/5.0"
        assert browser_user_agent("") == "Mozilla/5.0"
