"""Порты репозиториев, которыми пользуются сценарии."""

from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.moment_repository import MomentRepository
from backend.application.interface.repositories.notification_repository import (
    NotificationRepository,
)
from backend.application.interface.repositories.rating_repository import RatingRepository
from backend.application.interface.repositories.reaction_repository import ReactionRepository
from backend.application.interface.repositories.support_repository import SupportRepository
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.repositories.watch_repository import WatchRepository

__all__ = [
    "CollectionRepository",
    "FavoriteRepository",
    "HighlightRepository",
    "MomentRepository",
    "NotificationRepository",
    "RatingRepository",
    "ReactionRepository",
    "SupportRepository",
    "UserRepository",
    "WatchRepository",
]
