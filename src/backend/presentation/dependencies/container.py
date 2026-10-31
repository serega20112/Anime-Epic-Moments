"""Доступ к контейнеру dishka из обработчиков и middleware.

Единственная точка, где presentation достаёт зависимости из контейнера:
вне её код приложения не должен обращаться к ``request.state`` напрямую.
"""

from __future__ import annotations

from dishka import AsyncContainer
from fastapi import Request

from backend.domain.aggregates.user.user import User


class ContainerUnavailableError(RuntimeError):
    """Контейнер зависимостей не найден для текущего запроса."""


async def get_container(request: Request) -> AsyncContainer:
    """Получить request-scoped контейнер dishka.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        AsyncContainer: Контейнер текущего запроса.

    Raises:
        ContainerUnavailableError: Контейнер не создан для этого запроса.
    """
    container = getattr(request.state, "dishka_container", None)
    if container is None:
        raise ContainerUnavailableError("Контейнер dishka недоступен для запроса")
    return container


async def resolve[T](request: Request, dependency: type[T]) -> T:
    """Разрешить зависимость из контейнера dishka.

    Args:
        request: Текущий HTTP-запрос.
        dependency: Тип зависимости.

    Returns:
        T: Разрешённая зависимость.

    Raises:
        ContainerUnavailableError: Контейнер недоступен либо зависимость
            не зарегистрирована.

    Note:
        Захват широкий намеренно: это единственная точка, где presentation
        касается контейнера dishka, и любой отказ разрешения должен для
        вызывающего кода выглядеть одинаково — как недоступная зависимость,
        а не как один из десятков внутренних исключений dishka.
    """
    container = await get_container(request)
    try:
        return await container.get(dependency)
    except Exception as error:
        raise ContainerUnavailableError(
            f"Зависимость {dependency.__name__} не зарегистрирована в контейнере"
        ) from error


async def require_user(request: Request) -> User | None:
    """Получить авторизованного пользователя запроса.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        User | None: Пользователь сессии либо None для гостя.
    """
    return getattr(request.state, "user", None)
