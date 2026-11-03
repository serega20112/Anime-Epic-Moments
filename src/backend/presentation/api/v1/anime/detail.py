"""JSON-маршрут детальной карточки тайтла для мобильного клиента."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.watch.page.get_anime_detail import GetAnimeDetailUseCase
from backend.domain.value_objects.watch.detail import AnimeDetail
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.watch_mapper import map_watch_page_query
from backend.presentation.api.responses.anime_responses import AnimeCardResponse
from backend.presentation.api.responses.watch_responses import (
    AnimeDetailResponse,
    EpisodeProgressResponse,
    SourceResponse,
)
from backend.presentation.api.v1.watch_route.helpers import ERROR_RESPONSES

detail_router = APIRouter(route_class=DishkaRoute)


@detail_router.get(
    "/{anime_id}",
    name="api_anime.get_detail",
    response_model=AnimeDetailResponse,
    responses=ERROR_RESPONSES,
)
async def get_detail(
    request: Request,
    anime_id: int,
    use_case: FromDishka[GetAnimeDetailUseCase],
):
    """Отдать карточку тайтла с сериями, источниками и состояниями зрителя.

    Гостю доступна та же карточка без персональных полей: сценарий различает
    зрителя по идентификатору сессии, а не по содержимому запроса.

    Args:
        request: Текущий HTTP-запрос с необязательными параметрами серии.
        anime_id: Идентификатор аниме из пути.
        use_case: Сценарий карточки тайтла.

    Returns:
        AnimeDetailResponse: Карточка тайтла в мобильном представлении.
    """
    user = await get_current_user(request)
    detail = await use_case.execute(
        map_watch_page_query(request, anime_id=anime_id, user_id=user.id if user else None)
    )
    return build_detail_response(detail)


def build_detail_response(detail: AnimeDetail) -> AnimeDetailResponse:
    """Спроектировать доменную карточку тайтла в ответ мобильного маршрута.

    Проекция не содержит бизнес-решений: они приняты сценарием, здесь лишь
    раскладываются по полям JSON-контракта.

    Args:
        detail: Доменная карточка тайтла с прогрессом и избранным.

    Returns:
        AnimeDetailResponse: Ответ карточки тайтла.
    """
    page = detail.page
    return AnimeDetailResponse(
        anime=AnimeCardResponse(
            external_id=page.anime_id,
            title=page.anime_title,
            original_title=page.anime_title_original,
            description=page.anime_description,
            genres=page.genres,
            year=page.anime_year,
            rating=page.anime_rating,
            cover_url=page.anime_cover,
            episode_count=page.episode_total,
        ),
        episode=page.episode,
        episode_total=page.episode_total,
        episodes=[EpisodeProgressResponse.model_validate(item) for item in detail.episodes],
        sources=[
            SourceResponse(
                episode_number=source.episode,
                translation=source.translation_name,
                quality=source.quality_label,
                source_type=source.source_type,
                url=source.stream_url,
            )
            for source in page.sources
        ],
        favorites=detail.favorites,
        user_rating=page.user_rating,
        watch_status=page.current_status,
        last_position_seconds=page.last_position_seconds,
    )
