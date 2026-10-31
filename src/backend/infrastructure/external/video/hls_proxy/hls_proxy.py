"""Переписывание HLS-манифестов, чтобы сегменты шли через прокси."""

from __future__ import annotations

import re
from collections.abc import Callable
from urllib.parse import urljoin

_WrappedCitation = re.compile(r'URI="(?P<uri>[^"]+)"')


async def rewrite_hls_manifest(
    manifest_text: str,
    upstream_url: str,
    proxy_url_builder: Callable[[str], str],
) -> str:
    """Переписать адреса сегментов и атрибутов в HLS-манифесте."""
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
    """Переписать значения атрибута URI в строке манифеста."""

    def replace(match) -> str:
        """Заменить найденный URI абсолютным адресом через прокси."""
        absolute_url = urljoin(upstream_url, match.group("uri"))
        return f'URI="{proxy_url_builder(absolute_url)}"'

    return _WrappedCitation.sub(replace, line)
