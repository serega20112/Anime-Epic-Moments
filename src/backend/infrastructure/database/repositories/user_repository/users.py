"""Реализация репозитория: класс пакета и сборка mixin'ов по агрегатам."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interface.repositories.user_repository import (
    UserRepository as UserRepositoryPort,
)
from backend.domain import User
from backend.infrastructure.database.models import UserFollowModel, UserModel


class UserRepository(UserRepositoryPort):
    """Доступ к данным пользователей и подписок."""

    def __init__(self, session: AsyncSession):
        """Сохранить сессию запроса, через которую работает репозиторий."""
        self.session = session

    async def add(self, user: User):
        """Добавить пользователя и подставить сгенерированный идентификатор."""
        db_user = UserModel(
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            avatar_url=user.avatar_url,
            status=user.status,
            show_watch_activity=user.show_watch_activity,
            show_recent_episodes=user.show_recent_episodes,
        )
        self.session.add(db_user)
        await self.session.flush()
        user.id = db_user.id
        user.created_at = db_user.created_at
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        """Загрузить пользователя по идентификатору."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        return await self._to_entity(db_user) if db_user else None

    async def get_by_email(self, email: str) -> User | None:
        """Загрузить пользователя по адресу почты."""
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        db_user = result.scalar_one_or_none()
        return await self._to_entity(db_user) if db_user else None

    async def get_by_ids(self, user_ids: list[int]) -> list[User]:
        """Загрузить пользователей с указанными идентификаторами."""
        if not user_ids:
            return []
        result = await self.session.execute(select(UserModel).where(UserModel.id.in_(user_ids)))
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def update(self, user: User) -> User:
        """Обновить поля профиля пользователя."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == user.id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise ValueError("Пользователь для обновления не найден")
        db_user.username = user.username
        db_user.avatar_url = user.avatar_url
        db_user.status = user.status
        db_user.show_watch_activity = user.show_watch_activity
        db_user.show_recent_episodes = user.show_recent_episodes
        await self.session.flush()
        return user

    async def update_password(self, user_id: int, password_hash: str) -> User:
        """Обновить хеш пароля пользователя."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise ValueError("Пользователь для обновления не найден")
        db_user.password_hash = password_hash
        await self.session.flush()
        return await self._to_entity(db_user)

    async def follow(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Создать подписку, если её ещё нет."""
        if follower_user_id == followed_user_id:
            raise ValueError("Нельзя подписаться на самого себя")
        result = await self.session.execute(
            select(UserFollowModel.id).where(
                UserFollowModel.follower_user_id == follower_user_id,
                UserFollowModel.followed_user_id == followed_user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            self.session.add(
                UserFollowModel(
                    follower_user_id=follower_user_id,
                    followed_user_id=followed_user_id,
                )
            )
            await self.session.flush()
        return True

    async def unfollow(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Удалить подписку, если она есть."""
        if follower_user_id == followed_user_id:
            raise ValueError("Нельзя отписаться от самого себя")
        result = await self.session.execute(
            select(UserFollowModel).where(
                UserFollowModel.follower_user_id == follower_user_id,
                UserFollowModel.followed_user_id == followed_user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            await self.session.delete(existing)
            await self.session.flush()
        return False

    async def is_following(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Проверить, существует ли подписка."""
        if follower_user_id == followed_user_id:
            return False
        result = await self.session.execute(
            select(UserFollowModel.id).where(
                UserFollowModel.follower_user_id == follower_user_id,
                UserFollowModel.followed_user_id == followed_user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_follow_stats(self, user_id: int) -> tuple[int, int]:
        """Вернуть число подписчиков и подписок пользователя."""
        followers_result = await self.session.execute(
            select(func.count(UserFollowModel.id)).where(
                UserFollowModel.followed_user_id == user_id
            )
        )
        following_result = await self.session.execute(
            select(func.count(UserFollowModel.id)).where(
                UserFollowModel.follower_user_id == user_id
            )
        )
        followers_count = int(followers_result.scalar() or 0)
        following_count = int(following_result.scalar() or 0)
        return followers_count, following_count

    async def get_followed_user_ids(self, follower_user_id: int) -> list[int]:
        """Вернуть идентификаторы пользователей, на которых подписан зритель."""
        result = await self.session.execute(
            select(UserFollowModel.followed_user_id)
            .where(UserFollowModel.follower_user_id == follower_user_id)
            .order_by(UserFollowModel.created_at.desc())
        )
        return [int(value) for value in result.scalars().all()]

    async def get_followed_users(self, follower_user_id: int, limit: int = 12) -> list[User]:
        """Вернуть пользователей, на которых подписан зритель."""
        result = await self.session.execute(
            select(UserModel)
            .join(
                UserFollowModel,
                UserFollowModel.followed_user_id == UserModel.id,
            )
            .where(UserFollowModel.follower_user_id == follower_user_id)
            .order_by(UserFollowModel.created_at.desc())
            .limit(limit)
        )
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_followers(self, followed_user_id: int, limit: int = 12) -> list[User]:
        """Вернуть подписчиков пользователя."""
        result = await self.session.execute(
            select(UserModel)
            .join(
                UserFollowModel,
                UserFollowModel.follower_user_id == UserModel.id,
            )
            .where(UserFollowModel.followed_user_id == followed_user_id)
            .order_by(UserFollowModel.created_at.desc())
            .limit(limit)
        )
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def _to_entity(self, db_user: UserModel) -> User:
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            password_hash=db_user.password_hash,
            avatar_url=db_user.avatar_url,
            status=db_user.status,
            show_watch_activity=db_user.show_watch_activity,
            show_recent_episodes=db_user.show_recent_episodes,
            created_at=db_user.created_at,
        )
