"""Фасад подпакета инфраструктурных кэшей."""

from __future__ import annotations

from backend.infrastructure.cache.highlight_dashboard_cache import HighlightDashboardCache
from backend.infrastructure.cache.recommendation_cache import RecommendationCache
from backend.infrastructure.cache.ttl_cache import TTLCache
from backend.infrastructure.cache.watch_source_caches import WatchSourceCaches

__all__ = [
    "HighlightDashboardCache",
    "RecommendationCache",
    "TTLCache",
    "WatchSourceCaches",
]
