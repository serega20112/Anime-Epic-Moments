"""Модели ответов проб живости и готовности."""

from __future__ import annotations

from pydantic import BaseModel

LIVENESS_STATUS = "ok"


class LivenessResponse(BaseModel):
    """Ответ пробы живости процесса.

    Attributes:
        status: Метка ``ok``, подтверждающая, что процесс отвечает.
    """

    status: str = LIVENESS_STATUS


class ReadinessResponse(BaseModel):
    """Ответ пробы готовности с разбором по зависимостям.

    Attributes:
        status: Итог: ``ready`` либо ``unavailable``.
        checks: Отметка по каждой зависимости (``database``, ``redis``).
    """

    status: str
    checks: dict[str, str] = {}
