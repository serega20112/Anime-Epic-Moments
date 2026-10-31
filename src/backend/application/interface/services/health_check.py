"""Порт проверки готовности приложения к работе.

Пробы оркестратора (Kubernetes, Render, docker healthcheck) не должны знать,
как именно пингуются база и кэш: им нужен ответ «готов/не готов» и пометка по
каждой зависимости. Реализация живёт в инфраструктуре, контракт — здесь.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

READY_STATUS = "ready"
UNAVAILABLE_STATUS = "unavailable"
OK_MARK = "ok"
UNREACHABLE_MARK = "unreachable"
DISABLED_MARK = "disabled"


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Итог проверки зависимостей приложения.

    Attributes:
        ready: Готово ли приложение принимать трафик.
        checks: Отметка по каждой зависимости (``database``, ``redis``).
    """

    ready: bool
    checks: dict[str, str] = field(default_factory=dict)

    @property
    def payload(self) -> dict[str, object]:
        """Тело ответа для JSON-пробы.

        Returns:
            dict[str, object]: Статус готовности и разбор по зависимостям.
        """
        return {"status": READY_STATUS if self.ready else UNAVAILABLE_STATUS, "checks": self.checks}


class HealthCheckPort(ABC):
    """Контракт проверки готовности."""

    @abstractmethod
    async def check(self) -> HealthStatus:
        """Опросить зависимости и вернуть сводный статус.

        Returns:
            HealthStatus: Итог проверки с отметкой по каждой зависимости.
        """
