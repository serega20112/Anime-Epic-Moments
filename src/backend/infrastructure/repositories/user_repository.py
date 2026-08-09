from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import User
from backend.infrastructure.models import UserFollowModel, UserModel
from backend.infrastructure.repositories._async import repository_method


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @repository_method
    def add(self, user: User):
        db_user = UserModel(
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            avatar_url=user.avatar_url,
        )
        self.session.add(db_user)
        self.session.commit()
        user.id = db_user.id
        user.created_at = db_user.created_at
        return user

    @repository_method
    def get_by_id(self, user_id: int) -> User | None:
        db_user = self.session.query(UserModel).filter_by(id=user_id).first()
        if not db_user:
            return None
        return self._to_entity(db_user)

    @repository_method
    def get_by_email(self, email: str) -> User | None:
        db_user = self.session.query(UserModel).filter_by(email=email).first()
        if not db_user:
            return None
        return self._to_entity(db_user)

    @repository_method
    def get_by_ids(self, user_ids: list[int]) -> list[User]:
        if not user_ids:
            return []
        rows = self.session.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
        return [self._to_entity(row) for row in rows]

    @repository_method
    def update(self, user: User) -> User:
        """Обновляет username и avatar_url пользователя."""
        db_user = self.session.query(UserModel).filter_by(id=user.id).first()
        if not db_user:
            raise ValueError("Пользователь для обновления не найден")
        db_user.username = user.username
        db_user.avatar_url = user.avatar_url
        self.session.commit()
        return user

    @repository_method
    def update_password(self, user_id: int, password_hash: str) -> User:
        """Обновляет password_hash пользователя."""
        db_user = self.session.query(UserModel).filter_by(id=user_id).first()
        if not db_user:
            raise ValueError("Пользователь для обновления не найден")
        db_user.password_hash = password_hash
        self.session.commit()
        return self._to_entity(db_user)

    @repository_method
    def follow(self, follower_user_id: int, followed_user_id: int) -> bool:
        if follower_user_id == followed_user_id:
            raise ValueError("Нельзя подписаться на самого себя")
        existing = (
            self.session.query(UserFollowModel)
            .filter_by(
                follower_user_id=follower_user_id,
                followed_user_id=followed_user_id,
            )
            .first()
        )
        if existing is None:
            self.session.add(
                UserFollowModel(
                    follower_user_id=follower_user_id,
                    followed_user_id=followed_user_id,
                )
            )
            self.session.commit()
        return True

    @repository_method
    def unfollow(self, follower_user_id: int, followed_user_id: int) -> bool:
        if follower_user_id == followed_user_id:
            raise ValueError("Нельзя отписаться от самого себя")
        existing = (
            self.session.query(UserFollowModel)
            .filter_by(
                follower_user_id=follower_user_id,
                followed_user_id=followed_user_id,
            )
            .first()
        )
        if existing is not None:
            self.session.delete(existing)
            self.session.commit()
        return False

    @repository_method
    def is_following(self, follower_user_id: int, followed_user_id: int) -> bool:
        if follower_user_id == followed_user_id:
            return False
        return (
                self.session.query(UserFollowModel.id)
                .filter_by(
                    follower_user_id=follower_user_id,
                    followed_user_id=followed_user_id,
                )
                .first()
                is not None
        )

    @repository_method
    def get_follow_stats(self, user_id: int) -> tuple[int, int]:
        """Return follower and following counts for a user.

        Args:
            user_id: User identifier.

        Returns:
            tuple[int, int]: (followers, following).
        """
        followers_count = (
                self.session.query(func.count(UserFollowModel.id))
                .filter(UserFollowModel.followed_user_id == user_id)
                .scalar()
                or 0
        )
        following_count = (
                self.session.query(func.count(UserFollowModel.id))
                .filter(UserFollowModel.follower_user_id == user_id)
                .scalar()
                or 0
        )
        return int(followers_count), int(following_count)

    @repository_method
    def get_followed_user_ids(self, follower_user_id: int) -> list[int]:
        rows = (
            self.session.query(UserFollowModel.followed_user_id)
            .filter(UserFollowModel.follower_user_id == follower_user_id)
            .order_by(UserFollowModel.created_at.desc())
            .all()
        )
        return [int(value) for (value,) in rows]

    @repository_method
    def get_followed_users(self, follower_user_id: int, limit: int = 12) -> list[User]:
        rows = (
            self.session.query(UserModel)
            .join(
                UserFollowModel,
                UserFollowModel.followed_user_id == UserModel.id,
            )
            .filter(UserFollowModel.follower_user_id == follower_user_id)
            .order_by(UserFollowModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_entity(row) for row in rows]

    @repository_method
    def get_followers(self, followed_user_id: int, limit: int = 12) -> list[User]:
        rows = (
            self.session.query(UserModel)
            .join(
                UserFollowModel,
                UserFollowModel.follower_user_id == UserModel.id,
            )
            .filter(UserFollowModel.followed_user_id == followed_user_id)
            .order_by(UserFollowModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_entity(row) for row in rows]

    def _to_entity(self, db_user: UserModel) -> User:
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            password_hash=db_user.password_hash,
            avatar_url=db_user.avatar_url,
            created_at=db_user.created_at,
        )
