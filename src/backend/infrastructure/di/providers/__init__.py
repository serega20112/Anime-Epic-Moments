"""Dishka provider registry for all application dependencies."""

from backend.infrastructure.di.providers.anime import AnimeUseCaseProvider
from backend.infrastructure.di.providers.app import AppProvider
from backend.infrastructure.di.providers.auth import AuthUseCaseProvider
from backend.infrastructure.di.providers.collection import CollectionUseCaseProvider
from backend.infrastructure.di.providers.favorite import FavoriteUseCaseProvider
from backend.infrastructure.di.providers.highlight import HighlightUseCaseProvider
from backend.infrastructure.di.providers.moment import MomentUseCaseProvider
from backend.infrastructure.di.providers.reaction import ReactionUseCaseProvider
from backend.infrastructure.di.providers.request import RequestProvider
from backend.infrastructure.di.providers.support import SupportUseCaseProvider
from backend.infrastructure.di.providers.user import UserUseCaseProvider
from backend.infrastructure.di.providers.watch import WatchUseCaseProvider

__all__ = [
    "AnimeUseCaseProvider",
    "AppProvider",
    "AuthUseCaseProvider",
    "CollectionUseCaseProvider",
    "FavoriteUseCaseProvider",
    "HighlightUseCaseProvider",
    "MomentUseCaseProvider",
    "ReactionUseCaseProvider",
    "RequestProvider",
    "SupportUseCaseProvider",
    "UserUseCaseProvider",
    "WatchUseCaseProvider",
]
