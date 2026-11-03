"""JSON-маршрут ленты хайлайтов для мобильного клиента.

Лента отдаётся в режиме ``for_you``, ``following`` или ``top`` и страницей
общего контракта пагинации. Выборку, нарезку окна и общий счётчик считает
сценарий; маршрут лишь разбирает параметры запроса и сериализует карточки.
"""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto.highlight import MobileHighlightFeedQuery
from backend.application.use_cases.highlight.feed.get_mobile_highlight_feed import (
    GetMobileHighlightFeedUseCase,
)
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.responses.highlight_responses import (
    HighlightFeedPageResponse,
    MobileHighlightCardResponse,
)
from backend.presentation.api.v1.watch_route.helpers import ERROR_RESPONSES

feed_router = APIRouter(route_class=DishkaRoute)

DEFAULT_MODE = "for_you"
DEFAULT_PER_PAGE = 12
MAX_PER_PAGE = 50
MAX_PAGE = 1000


@feed_router.get(
    "/feed",
    name="api_highlights.feed",
    response_model=HighlightFeedPageResponse,
    responses=ERROR_RESPONSES,
)
async def highlights_feed(
    request: Request,
    use_case: FromDishka[GetMobileHighlightFeedUseCase],
):
    """Отдать страницу ленты хайлайтов в выбранном режиме.

    Args:
        request: Текущий HTTP-запрос с параметрами режима и пагинации.
        use_case: Сценарий мобильной ленты хайлайтов.

    Returns:
        HighlightFeedPageResponse: Страница карточек с метаданными навигации.
    """
    user = await get_current_user(request)
    page = await use_case.execute(
        build_mobile_feed_query(request, viewer_user_id=user.id if user else None)
    )
    return HighlightFeedPageResponse(
        items=[MobileHighlightCardResponse.model_validate(card) for card in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        total_pages=page.total_pages,
        has_next=page.has_next,
        has_previous=page.has_previous,
    )


def build_mobile_feed_query(
    request: Request, *, viewer_user_id: int | None
) -> MobileHighlightFeedQuery:
    """Собрать запрос мобильной ленты из параметров строки запроса.

    Args:
        request: Текущий HTTP-запрос.
        viewer_user_id: Идентификатор зрителя либо None для гостя.

    Returns:
        MobileHighlightFeedQuery: Режим, страница и зритель ленты.
    """
    params = request.query_params
    return MobileHighlightFeedQuery(
        mode=str(params.get("mode") or DEFAULT_MODE).strip() or DEFAULT_MODE,
        page=_clamped_int(params.get("page"), default=1, minimum=1, maximum=MAX_PAGE),
        per_page=_clamped_int(
            params.get("per_page"), default=DEFAULT_PER_PAGE, minimum=1, maximum=MAX_PER_PAGE
        ),
        include_spoilers=str(params.get("include_spoilers") or "").lower() in {"1", "true", "yes"},
        viewer_user_id=viewer_user_id,
    )


def _clamped_int(value: str | None, *, default: int, minimum: int, maximum: int) -> int:
    """Разобрать целое и ограничить его допустимым диапазоном.

    Args:
        value: Сырое значение параметра строки запроса.
        default: Значение при отсутствии или сбое разбора.
        minimum: Нижняя граница.
        maximum: Верхняя граница.

    Returns:
        int: Число внутри диапазона.
    """
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))
