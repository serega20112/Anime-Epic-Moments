"""Поиск актуального endpoint списка качеств в JS-бандле плеера Kodik.

Kodik периодически переименовывает ручку списка качеств и зашивает её адрес в
JS-бандл плеера в base64. Захардкодить адрес нельзя, поэтому имя бандла
достаётся со страницы плеера, а внутри бандла ищется ``url:atob("...")``.
"""

from __future__ import annotations

import base64
import re
from urllib.parse import urljoin

import httpx

DEFAULT_VIDEO_INFO_ENDPOINT = "/ftor"


async def discover_video_info_endpoint(
    session: httpx.AsyncClient,
    normalized_link: str,
    fallback: str = "/kor",
) -> str | None:
    """Вычисляет текущий endpoint списка качеств.

    Args:
        session: HTTP-клиент провайдера.
        normalized_link: Нормализованная ссылка на материал Kodik.
        fallback: Значение, если бандл найден, но адрес в нём не разобран.

    Returns:
        str | None: Путь endpoint'а либо None, если страница или бандл не
        отдали содержимое.
    """
    try:
        player_page = await session.get(normalized_link)
        player_page.raise_for_status()
        page_text = player_page.text
    except httpx.HTTPError:
        return None

    player_chunk_match = re.search(
        r'src="(?P<link>/assets/js/app\.player_single\.[a-z0-9]+\.js)"',
        page_text,
        flags=re.IGNORECASE,
    )
    if not player_chunk_match:
        return None

    chunk_url = urljoin(normalized_link, player_chunk_match.group("link"))
    try:
        chunk_response = await session.get(chunk_url)
        chunk_response.raise_for_status()
        chunk_text = chunk_response.text
    except httpx.HTTPError:
        return None

    endpoint_match = re.search(
        r'type:"POST",url:atob\("(?P<b64str>[^"]+)"\)',
        chunk_text,
        flags=re.IGNORECASE,
    )
    if not endpoint_match:
        return fallback

    try:
        decoded = base64.b64decode(endpoint_match.group("b64str")).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return fallback
    return decoded or fallback
