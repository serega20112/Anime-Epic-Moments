"""Фасад подпакета проб готовности приложения."""

from __future__ import annotations

from backend.infrastructure.health.health_check import ApplicationHealthCheck

__all__ = ["ApplicationHealthCheck"]
