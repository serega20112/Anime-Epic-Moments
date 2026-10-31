"""Сценарий публичного профиля пользователя."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from starlette import status

from backend.application.dto import ProfileOverviewQuery, PublicProfileQuery
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.profile.get_profile_overview import (
    GetProfileOverviewUseCase,
)
from backend.application.use_cases.result import UseCaseResult
from backend.domain import (
    FollowUserCard,
    PublicProfileOverview,
    User,
)
from backend.domain.aggregates.collection.collection import AnimeCollection
from backend.domain.exceptions import NotFoundError
from backend.domain.value_objects.collection.cards import CollectionCard

FOLLOW_PREVIEW_LIMIT = 6


@dataclass(frozen=True, slots=True)
class _PublicProfileState:
    """Данные публичного профиля, прочитанные из базы за одну транзакцию.

    Attributes:
        followers_count: Число подписчиков владельца профиля.
        following_count: Число подписок владельца профиля.
        collections: Публичные коллекции владельца профиля.
        items_count_map: Число элементов по идентификаторам коллекций.
        followers: Подписчики владельца профиля для превью.
        following: Подписки владельца профиля для превью.
        is_following: Признак подписки зрителя на владельца профиля.
    """

    followers_count: int
    following_count: int
    collections: list[AnimeCollection]
    items_count_map: Mapping[int, int]
    followers: list[User]
    following: list[User]
    is_following: bool


class GetPublicProfileOverviewUseCase:
    """Собирает публичный профиль пользователя с коллекциями и социальной статистикой."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_use_case: GetProfileOverviewUseCase,
    ) -> None:
        """Инициализирует сценарий получения публичного обзора профиля.

        Args:
            unit_of_work: Граница транзакции чтения профиля и коллекций.
            profile_overview_use_case: Сценарий получения обзора профиля.
        """
        self._unit_of_work = unit_of_work
        self._profile_overview_use_case = profile_overview_use_case

    async def execute(self, query: PublicProfileQuery) -> UseCaseResult:
        """Собрать публичный обзор профиля.

        Обзор профиля собирается до транзакции публичных данных, чтобы кэш и
        обращения к каталогу не удерживали соединение с базой.

        Args:
            query: Идентификатор профиля и идентификатор зрителя.

        Returns:
            UseCaseResult: Публичный обзор либо ошибка 404 при отсутствии профиля.
        """
        try:
            profile = await self._profile_overview_use_case.execute(
                ProfileOverviewQuery(user_id=query.profile_user_id)
            )
        except NotFoundError:
            return UseCaseResult.failure(
                "Пользователь не найден", status_code=status.HTTP_404_NOT_FOUND
            )
        state = await self._load_state(query)
        return UseCaseResult.success(
            PublicProfileOverview(
                profile=profile,
                public_collections=self._build_collections(state),
                followers_preview=[
                    self._build_user_card(user) for user in state.followers if user.id is not None
                ],
                following_preview=[
                    self._build_user_card(user) for user in state.following if user.id is not None
                ],
                followers_count=state.followers_count,
                following_count=state.following_count,
                is_following=state.is_following,
                can_follow=self._can_follow(query),
            )
        )

    async def _load_state(self, query: PublicProfileQuery) -> _PublicProfileState:
        """Прочитать данные публичного профиля одной транзакцией.

        Args:
            query: Идентификатор профиля и идентификатор зрителя.

        Returns:
            _PublicProfileState: Прочитанные статистика, коллекции и подписки.
        """
        async with self._unit_of_work as uow:
            user_repository = uow.repository(UserRepository)
            collection_repository = uow.repository(CollectionRepository)
            followers_count, following_count = await user_repository.get_follow_stats(
                query.profile_user_id
            )
            collections = await collection_repository.get_public_user_collections(
                query.profile_user_id
            )
            items_count_map = await collection_repository.get_items_count_map(
                [item.id for item in collections if item.id is not None]
            )
            followers = await user_repository.get_followers(
                query.profile_user_id, limit=FOLLOW_PREVIEW_LIMIT
            )
            following = await user_repository.get_followed_users(
                query.profile_user_id, limit=FOLLOW_PREVIEW_LIMIT
            )
            is_following = await self._check_following(user_repository, query)
        return _PublicProfileState(
            followers_count=followers_count,
            following_count=following_count,
            collections=collections,
            items_count_map=items_count_map,
            followers=followers,
            following=following,
            is_following=is_following,
        )

    @staticmethod
    async def _check_following(user_repository: UserRepository, query: PublicProfileQuery) -> bool:
        """Проверить, подписан ли зритель на владельца профиля.

        Args:
            user_repository: Репозиторий пользователей.
            query: Идентификатор профиля и идентификатор зрителя.

        Returns:
            bool: True, если зритель подписан на профиль.
        """
        viewer_user_id = query.viewer_user_id
        if viewer_user_id is None or viewer_user_id == query.profile_user_id:
            return False
        return await user_repository.is_following(viewer_user_id, query.profile_user_id)

    @staticmethod
    def _can_follow(query: PublicProfileQuery) -> bool:
        """Оценить, может ли зритель подписаться на профиль.

        Args:
            query: Идентификатор профиля и идентификатор зрителя.

        Returns:
            bool: True для авторизованного зрителя чужого профиля.
        """
        return query.viewer_user_id is not None and query.viewer_user_id != query.profile_user_id

    @staticmethod
    def _build_collections(state: _PublicProfileState) -> list[CollectionCard]:
        """Собрать карточки публичных коллекций со счётчиками элементов.

        Args:
            state: Прочитанные данные публичного профиля.

        Returns:
            list[CollectionCard]: Карточки коллекций для публичного профиля.
        """
        return [
            CollectionCard(
                id=collection.id,
                title=collection.title,
                description=collection.description,
                items_count=state.items_count_map.get(collection.id or 0, 0),
                is_public=collection.is_public,
                created_at=collection.created_at.strftime("%Y-%m-%d"),
                share_url=f"/collections/share/{collection.id}",
            )
            for collection in state.collections
            if collection.id is not None
        ]

    @staticmethod
    def _build_user_card(user: User) -> FollowUserCard:
        """Собрать карточку пользователя для превью подписок.

        Args:
            user: Пользователь списка подписок.

        Returns:
            FollowUserCard: Карточка пользователя со ссылкой на профиль.
        """
        return FollowUserCard(
            user_id=user.id or 0,
            username=user.username,
            avatar_url=user.avatar_url,
            profile_url=f"/users/{user.id}",
        )
