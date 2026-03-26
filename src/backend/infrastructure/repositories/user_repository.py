from sqlalchemy.orm import Session
from src.backend.infrastructure.models.sqlalchemy_models import UserModel
from src.backend.domain.user.entity import User
from typing import Optional


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

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

    def get_by_id(self, user_id: int) -> Optional[User]:
        db_user = self.session.query(UserModel).filter_by(id=user_id).first()
        if not db_user:
            return None
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            password_hash=db_user.password_hash,
            avatar_url=db_user.avatar_url,
            created_at=db_user.created_at,
        )

    def get_by_email(self, email: str) -> Optional[User]:
        db_user = self.session.query(UserModel).filter_by(email=email).first()
        if not db_user:
            return None
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            password_hash=db_user.password_hash,
            avatar_url=db_user.avatar_url,
            created_at=db_user.created_at,
        )

    def update(self, user: User) -> User:
        """Обновляет username и avatar_url пользователя."""
        db_user = self.session.query(UserModel).filter_by(id=user.id).first()
        if not db_user:
            raise ValueError("Пользователь для обновления не найден")
        db_user.username = user.username
        db_user.avatar_url = user.avatar_url
        self.session.commit()
        return user

    def update_password(self, user_id: int, password_hash: str) -> User:
        """Обновляет password_hash пользователя."""
        db_user = self.session.query(UserModel).filter_by(id=user_id).first()
        if not db_user:
            raise ValueError("Пользователь для обновления не найден")
        db_user.password_hash = password_hash
        self.session.commit()
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            password_hash=db_user.password_hash,
            avatar_url=db_user.avatar_url,
            created_at=db_user.created_at,
        )
