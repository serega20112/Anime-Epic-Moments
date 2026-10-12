"""Rating routes: set user anime ratings from web forms."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.rating.set_user_anime_rating import SetUserAnimeRatingUseCase
from backend.presentation.api.auth_responses import flash, redirect

rating_router = APIRouter(prefix="/ratings", route_class=DishkaRoute)
rating_bp = rating_router


@rating_router.post("/", name="rating.rate_anime")
async def rate_anime(request: Request, use_case: FromDishka[SetUserAnimeRatingUseCase]):
    """Save or update the rating for an anime submitted from a web form.

    Args:
        request: Incoming HTTP request with a rating form.
        use_case: Set user anime rating use case.

    Returns:
        RedirectResponse: Redirect back to the anime page.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return await redirect(request, "auth.login_page")
    form = await request.form()
    anime_id_raw = str(form.get("anime_id") or "").strip()
    score_raw = str(form.get("score") or "").strip()
    if not anime_id_raw or not score_raw:
        await flash(request, "Оценка не сохранена: передайте рейтинг тайтла")
        return await redirect(request, "index.index")
    try:
        anime_id = int(anime_id_raw)
        score = int(score_raw)
    except ValueError:
        await flash(request, "Оценка не сохранена: некорректные параметры")
        return await redirect(request, "index.index")
    await use_case.execute(user_id=user.id, anime_id=anime_id, score=score)
    return await redirect(request, "watch.watch_page", anime_id=anime_id)
