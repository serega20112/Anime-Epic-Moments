from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import User
from backend.infrastructure.models import UserFollowModel, UserModel


class UserRepository:
    """Data access for users and their follow relations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user: User):
        """Add a new user and assign the generated identifier.

        Args:
            user: User aggregate to persist.

        Returns:
            User: The persisted user with the assigned id.
        """
        db_user = UserModel(
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            avatar_url=user.avatar_url,
        )
        self.session.add(db_user)
        await self.session.flush()
        user.id = db_user.id
        user.created_at = db_user.created_at
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        """Fetch a user by identifier.

        Args:
            user_id: User identifier.

        Returns:
            User | None: The user or None when missing.
        """
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        return self._to_entity(db_user) if db_user else None

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email.

        Args:
            email: User email.

        Returns:
            User | None: The user or None when missing.
        """
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        db_user = result.scalar_one_or_none()
        return self._to_entity(db_user) if db_user else None

    async def get_by_ids(self, user_ids: list[int]) -> list[User]:
        """Fetch users matching the given identifiers.

        Args:
            user_ids: User identifiers.

        Returns:
            list[User]: Matching users.
        """
        if not user_ids:
            return []
        result = await self.session.execute(select(UserModel).where(UserModel.id.in_(user_ids)))
        return [self._to_entity(row) for row in result.scalars().all()]

    async def update(self, user: User) -> User:
        """Update the username and avatar of a user.

        Args:
            user: User aggregate with updated fields.

        Returns:
            User: The updated user.
        """
        result = await self.session.execute(select(UserModel).where(UserModel.id == user.id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise ValueError("Пользователь для обновления не найден")
        db_user.username = user.username
        db_user.avatar_url = user.avatar_url
        await self.session.commit()
        return user

    async def update_password(self, user_id: int, password_hash: str) -> User:
        """Update the password hash of a user.

        Args:
            user_id: User identifier.
            password_hash: New password hash.

        Returns:
            User: The updated user.
        """
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise ValueError("Пользователь для обновления не найден")
        db_user.password_hash = password_hash
        await self.session.commit()
        return self._to_entity(db_user)

    async def follow(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Create a follow relation if it does not exist.

        Args:
            follower_user_id: Following user identifier.
            followed_user_id: Followed user identifier.

        Returns:
            bool: True always on success.
        """
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
            await self.session.commit()
        return True

    async def unfollow(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Remove a follow relation if it exists.

        Args:
            follower_user_id: Following user identifier.
            followed_user_id: Followed user identifier.

        Returns:
            bool: False always.
        """
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
            await self.session.commit()
        return False

    async def is_following(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Check whether a follow relation exists.

        Args:
            follower_user_id: Following user identifier.
            followed_user_id: Followed user identifier.

        Returns:
            bool: True if the relation exists.
        """
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
        """Return follower and following counts for a user.

        Args:
            user_id: User identifier.

        Returns:
            tuple[int, int]: (followers, following).
        """
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
        """Return identifiers of users followed by the given user.

        Args:
            follower_user_id: Following user identifier.

        Returns:
            list[int]: Followed user identifiers.
        """
        result = await self.session.execute(
            select(UserFollowModel.followed_user_id)
            .where(UserFollowModel.follower_user_id == follower_user_id)
            .order_by(UserFollowModel.created_at.desc())
        )
        return [int(value) for value in result.scalars().all()]

    async def get_followed_users(self, follower_user_id: int, limit: int = 12) -> list[User]:
        """Return users followed by the given user.

        Args:
            follower_user_id: Following user identifier.
            limit: Maximum number of users.

        Returns:
            list[User]: Followed users.
        """
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
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_followers(self, followed_user_id: int, limit: int = 12) -> list[User]:
        """Return followers of the given user.

        Args:
            followed_user_id: Followed user identifier.
            limit: Maximum number of users.

        Returns:
            list[User]: Followers.
        """
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
        return [self._to_entity(row) for row in result.scalars().all()]

    def _to_entity(self, db_user: UserModel) -> User:
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            password_hash=db_user.password_hash,
            avatar_url=db_user.avatar_url,
            created_at=db_user.created_at,
        )
