from __future__ import annotations

from backend.infrastructure.media_proxy.hls_proxy import rewrite_hls_manifest


def _proxy(url: str) -> str:
    return f"/proxy?url={url}"


class TestRewriteHlsManifest:
    async def test_rewrites_plain_segment_lines(self):
        manifest = "#EXTM3U\n#EXT-X-TARGETDURATION:10\nseg1.ts\nhttps://cdn.libria.fun/seg2.ts\n"
        base = "https://cdn.libria.fun/master.m3u8"
        result = await rewrite_hls_manifest(manifest, base, _proxy)
        lines = result.splitlines()
        assert "#EXTM3U" in result
        assert lines[2] == _proxy("https://cdn.libria.fun/seg1.ts")
        assert lines[3] == _proxy("https://cdn.libria.fun/seg2.ts")

    async def test_rewrites_uri_attributes(self):
        manifest = "#EXT-X-STREAM-INF:BANDWIDTH=800\nindex_480.m3u8"
        base = "https://cdn.libria.fun/master.m3u8"
        result = await rewrite_hls_manifest(manifest, base, _proxy)
        assert _proxy("https://cdn.libria.fun/index_480.m3u8") in result

    async def test_rewrites_wrapped_citation_uri(self):
        manifest = '#EXT-X-KEY:METHOD=AES-128,URI="key.bin"'
        base = "https://cdn.libria.fun/master.m3u8"
        result = await rewrite_hls_manifest(manifest, base, _proxy)
        assert 'URI="' + _proxy("https://cdn.libria.fun/key.bin") + '"' in result

    async def test_preserves_empty_lines_and_comments(self):
        manifest = "#EXTM3U\n\n#EXT-X-VERSION:3\n"
        result = await rewrite_hls_manifest(manifest, "https://cdn.libria.fun/m.m3u8", _proxy)
        assert result == "#EXTM3U\n\n#EXT-X-VERSION:3"

    async def test_keeps_absolute_segments_unchanged_shape(self):
        manifest = "https://cdn.libria.fun/seg.ts"
        result = await rewrite_hls_manifest(manifest, "https://cdn.libria.fun/m.m3u8", _proxy)
        assert result == _proxy("https://cdn.libria.fun/seg.ts")
