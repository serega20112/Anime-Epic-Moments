"""Построение ключей субъекта для ограничителей частоты запросов.

Ключ — часть HTTP-контракта (кто именно ограничивается: гость по IP, пользователь
по идентификатору, пар «IP + тайтл»), поэтому строители живут в presentation, а
инфраструктурный счётчик получает уже готовую строку.
"""

from __future__ import annotations

GUEST_SUFFIX = "guest"
USER_PREFIX = "user"


async def support_ticket_subject(*, ip_address: str, user_id: int | None) -> str:
    """Построить ключ субъекта для создания тикета поддержки.

    Args:
        ip_address: Адрес клиента.
        user_id: Идентификатор авторизованного пользователя либо None.

    Returns:
        str: Ключ субъекта ограничения.
    """
    if user_id:
        return f"{ip_address}::{USER_PREFIX}::{user_id}"
    return f"{ip_address}::{GUEST_SUFFIX}"


async def watch_anime_subject(*, ip_address: str, anime_id: int | None) -> str:
    """Построить ключ субъекта, привязанный к тайтлу.

    Args:
        ip_address: Адрес клиента.
        anime_id: Идентификатор аниме либо None.

    Returns:
        str: Ключ субъекта ограничения.
    """
    return f"{ip_address}::{anime_id or 'unknown'}"


async def watch_user_subject(*, ip_address: str, user_id: int | None) -> str:
    """Построить ключ субъекта по действующему пользователю.

    Args:
        ip_address: Адрес клиента.
        user_id: Идентификатор авторизованного пользователя либо None.

    Returns:
        str: Ключ субъекта ограничения.
    """
    if user_id:
        return f"{ip_address}::{user_id}"
    return f"{ip_address}::{GUEST_SUFFIX}"
