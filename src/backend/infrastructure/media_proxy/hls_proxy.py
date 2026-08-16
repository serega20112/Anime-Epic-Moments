"""HLS manifest rewriting so playlist segments flow through the proxy."""

from __future__ import annotations

import re
from collections.abc import Callable
from urllib.parse import urljoin

_WrappedCitation = re.compile(r'URI="(?P<uri>[^"]+)"')


def rewrite_hls_manifest(
    manifest_text: str,
    upstream_url: str,
    proxy_url_builder: Callable[[str], str],
) -> str:
    """Rewrite segment and attribute URIs in an HLS manifest.

    Args:
        manifest_text: Raw manifest text.
        upstream_url: Upstream URL for resolving relative URIs.
        proxy_url_builder: Callable mapping an absolute media URL to its proxy URL.

    Returns:
        str: Rewritten manifest text.
    """
    rewritten_lines: list[str] = []
    for line in manifest_text.splitlines():
        stripped = line.strip()
        if not stripped:
            rewritten_lines.append(line)
            continue
        if stripped.startswith("#"):
            rewritten_lines.append(_rewrite_uri_attributes(line, upstream_url, proxy_url_builder))
            continue
        absolute_url = urljoin(upstream_url, stripped)
        rewritten_lines.append(proxy_url_builder(absolute_url))
    return "\n".join(rewritten_lines)


def _rewrite_uri_attributes(
    line: str,
    upstream_url: str,
    proxy_url_builder: Callable[[str], str],
) -> str:
    """Rewrite URI attribute values inside an HLS manifest line.

    Args:
        line: Raw manifest line.
        upstream_url: Upstream URL for resolving relative URIs.
        proxy_url_builder: Callable mapping an absolute media URL to its proxy URL.

    Returns:
        str: Rewritten manifest line.
    """

    def replace(match) -> str:
        absolute_url = urljoin(upstream_url, match.group("uri"))
        return f'URI="{proxy_url_builder(absolute_url)}"'

    return _WrappedCitation.sub(replace, line)
