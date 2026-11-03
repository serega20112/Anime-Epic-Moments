"""Маршрут выставления оценок аниме из веб-форм."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto.rating import SetUserAnimeRatingCommand
from backend.application.use_cases.rating.set_user_anime_rating import SetUserAnimeRatingUseCase
from backend.presentation.api.auth_responses import flash, redirect
from backend.presentation.api.requests.form_models import read_form_model
from backend.presentation.api.requests.rating_requests import RateAnimeRequest

rating_form_router = APIRouter(route_class=DishkaRoute)


@rating_form_router.post("/", name="rating.rate_anime")
async def rate_anime(request: Request, use_case: FromDishka[SetUserAnimeRatingUseCase]):
    """Сохранить или обновить оценку аниме из формы.

    Args:
        request: Текущий HTTP-запрос с формой оценки.
        use_case: Сценарий выставления оценки.

    Returns:
        Response: Редирект на страницу просмотра либо обратно на главную с сообщением.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return await redirect(request, "auth.login_page")
    payload = await read_form_model(request, RateAnimeRequest)
    if payload is None:
        await flash(request, "Оценка не сохранена: некорректные параметры")
        return await redirect(request, "index.index")
    await use_case.execute(
        SetUserAnimeRatingCommand(user_id=user.id, anime_id=payload.anime_id, score=payload.score)
    )
    return await redirect(request, "watch.watch_page", anime_id=payload.anime_id)
