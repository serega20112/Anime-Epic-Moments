"""Порт проверки ID-токена Google для входа и привязки аккаунта."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    """Подтверждённая личность из ID-токена Google.

    Attributes:
        subject: Стабильный идентификатор аккаунта Google.
        email: Почта аккаунта Google.
        email_verified: Подтверждена ли почта в Google.
        name: Отображаемое имя либо пустая строка.
        picture: Ссылка на аватар либо пустая строка.
    """

    subject: str
    email: str
    email_verified: bool
    name: str = ""
    picture: str = ""


class GoogleAuthClientInterface(ABC):
    """Проверяет подлинность ID-токена Google и возвращает его заявления."""

    @abstractmethod
    async def verify_id_token(self, id_token: str) -> GoogleIdentity | None:
        """Проверить ID-токен и вернуть подтверждённую личность.

        Args:
            id_token: JWT-токен, полученный мобильным клиентом от Google.

        Returns:
            GoogleIdentity | None: Подтверждённая личность либо None, если токен
                недействителен, просрочен или адресован не нашему приложению.
        """
