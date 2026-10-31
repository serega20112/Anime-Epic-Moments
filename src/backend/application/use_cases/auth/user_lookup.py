"""Чтение пользователя по почте в границах транзакции сценария."""

from __future__ import annotations

from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import User


async def find_user_by_email(unit_of_work: UnitOfWorkInterface, email: str) -> User | None:
    """Прочитать пользователя по адресу почты короткой транзакцией.

    Сценарии аутентификации начинают именно с этого чтения и сразу отпускают
    соединение: дальше идут хеширование пароля и почта, которые не должны
    держать транзакцию открытой.

    Args:
        unit_of_work: Граница транзакции вызывающего сценария.
        email: Нормализованный адрес почты.

    Returns:
        User | None: Найденный пользователь либо None.
    """
    async with unit_of_work as uow:
        return await uow.repository(UserRepository).get_by_email(email)
