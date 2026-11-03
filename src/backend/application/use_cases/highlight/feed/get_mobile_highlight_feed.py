"""Сценарий ленты хайлайтов для мобильного клиента с режимами и пагинацией.

Режим ``top`` берёт публичный топ, ``following`` — хайлайты подписок зрителя,
``for_you`` — свежие публичные с добавлением лайкнутых для авторизованного.
Карточки собираются тем же механизмом, что и веба, а нарезка страницы и общий
счётчик живут здесь, поэтому presentation не принимает решений о выборке.
"""

from __future__ import annotations

from backend.application.dto.highlight import HighlightDashboardQuery, MobileHighlightFeedQuery
from backend.application.dto.highlight.mobile_highlight_feed_query import (
    FEED_MODES,
    MODE_FOLLOWING,
    MODE_FOR_YOU,
    MODE_TOP,
)
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.domain import Highlight, HighlightCard, MobileHighlightFeedPage

SORT_POPULAR = "popular"
SORT_RECENT = "recent"


class GetMobileHighlightFeedUseCase(GetUserHighlightsUseCase):
    """Собирает страницу ленты хайлайтов в выбранном режиме."""

    async def execute(self, query: MobileHighlightFeedQuery) -> MobileHighlightFeedPage:
        """Собрать страницу ленты с учётом режима и пагинации.

        Args:
            query: Режим, страница, размер страницы и зритель ленты.

        Returns:
            MobileHighlightFeedPage: Страница карточек с метаданными навигации.
        """
        page = max(query.page, 1)
        per_page = max(query.per_page, 1)
        window = page * per_page
        normalized_mode = query.mode if query.mode in FEED_MODES else MODE_FOR_YOU

        dashboard_query = HighlightDashboardQuery(
            sort_by=SORT_POPULAR if normalized_mode == MODE_TOP else SORT_RECENT,
            include_spoilers=query.include_spoilers,
            viewer_user_id=query.viewer_user_id,
            user_id=query.viewer_user_id,
        )
        async with self._unit_of_work as uow:
            repository = uow.repository(HighlightRepository)
            highlights = await self._load_by_mode(
                uow, repository, normalized_mode, query.viewer_user_id, window
            )
            engagement_map = await repository.get_engagement_map(
                [item.id for item in highlights if item.id is not None],
                viewer_user_id=query.viewer_user_id,
            )
            owner_map = await self._load_owners(uow, highlights)

        dashboard = await self._build_dashboard(
            highlights, dashboard_query, engagement_map, owner_map
        )
        cards = self._dedupe(dashboard.items)
        start = (page - 1) * per_page
        total = len(cards)
        total_pages = max(1, -(-total // per_page))
        return MobileHighlightFeedPage(
            items=cards[start : start + per_page],
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

    async def _load_by_mode(
        self,
        uow: UnitOfWorkInterface,
        repository: HighlightRepository,
        mode: str,
        viewer_user_id: int | None,
        window: int,
    ) -> list[Highlight]:
        """Загрузить хайлайты выбранного режима в объёме окна страницы.

        Args:
            uow: Граница транзакции для чтения подписок.
            repository: Репозиторий хайлайтов текущей транзакции.
            mode: Нормализованный режим ленты.
            viewer_user_id: Идентификатор зрителя либо None для гостя.
            window: Число записей, покрывающее запрошенную страницу.

        Returns:
            list[Highlight]: Хайлайты режима в порядке выборки.
        """
        if mode == MODE_TOP:
            return await repository.get_public_top(window)
        if mode == MODE_FOLLOWING:
            if viewer_user_id is None:
                return []
            followed = await uow.repository(UserRepository).get_followed_user_ids(viewer_user_id)
            if not followed:
                return []
            return await repository.get_by_users(followed, limit=window)
        recent = await repository.get_public_recent(window)
        if viewer_user_id is None:
            return recent
        liked = await repository.get_liked_by_user(viewer_user_id, limit=window)
        return self._dedupe_highlights(liked + recent)

    @staticmethod
    def _dedupe_highlights(highlights: list[Highlight]) -> list[Highlight]:
        """Убрать повторные хайлайты, сохраняя первый порядок.

        Args:
            highlights: Исходный список возможных дублей.

        Returns:
            list[Highlight]: Список без повторов по идентификатору.
        """
        seen: set[int] = set()
        result: list[Highlight] = []
        for item in highlights:
            key = item.id if item.id is not None else id(item)
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    @staticmethod
    def _dedupe(cards: list[HighlightCard]) -> list[HighlightCard]:
        """Убрать повторные карточки, сохраняя первый порядок.

        Args:
            cards: Карточки возможны с дублями из разных секций режима.

        Returns:
            list[HighlightCard]: Карточки без повторов по идентификатору.
        """
        seen: set[int] = set()
        result: list[HighlightCard] = []
        for card in cards:
            if card.id in seen:
                continue
            seen.add(card.id)
            result.append(card)
        return result
