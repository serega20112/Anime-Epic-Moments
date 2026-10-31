"""Маршруты проксирования медиапотока плеера."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import Response

from backend.infrastructure.external.video.hls_proxy import MediaProxyClient

media_proxy_router = APIRouter(route_class=DishkaRoute)


@media_proxy_router.get("/proxy", name="watch.proxy_stream")
@media_proxy_router.head("/proxy", name="watch.proxy_stream_head")
async def proxy_stream(
    request: Request,
    media_proxy_client: FromDishka[MediaProxyClient],
):
    """Проксировать медиапоток с проверкой адреса и переписыванием HLS.

    Args:
        request: Текущий HTTP-запрос.
        media_proxy_client: Клиент проксирования медиапотоков.

    Returns:
        Response: Ответ проксируемого источника с переписанным HLS.
    """
    upstream_url = str(request.query_params.get("url") or "").strip()
    if not upstream_url:
        return Response(status_code=HTTPStatus.BAD_REQUEST)

    def proxy_url_builder(absolute_url: str) -> str:
        """Собрать адрес прокси для исходного медиа-URL."""
        return f"{request.app.url_path_for('watch.proxy_stream')}?url={absolute_url}"

    return await media_proxy_client.proxy(
        request,
        upstream_url=upstream_url,
        proxy_url_builder=proxy_url_builder,
    )
