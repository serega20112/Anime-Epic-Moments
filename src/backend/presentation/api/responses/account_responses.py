"""Модели ответов управления учётной записью мобильного клиента."""

from __future__ import annotations

from pydantic import BaseModel


class AccountDeletedResponse(BaseModel):
    """Итог удаления аккаунта.

    Attributes:
        deleted: Флаг успешного удаления аккаунта.
    """

    deleted: bool


class ExportProfileResponse(BaseModel):
    """Раздел профиля в выгрузке данных.

    Attributes:
        id: Идентификатор пользователя.
        email: Адрес почты владельца.
        username: Отображаемое имя.
        status: Статус профиля либо None.
        created_at: Момент регистрации в ISO-формате либо None.
    """

    id: int
    email: str
    username: str
    status: str | None = None
    created_at: str | None = None


class ExportFavoriteResponse(BaseModel):
    """Избранная работа в выгрузке данных.

    Attributes:
        anime_id: Идентификатор аниме.
        title: Название на момент добавления.
    """

    anime_id: int
    title: str


class ExportStatusResponse(BaseModel):
    """Запись дневника просмотра в выгрузке данных.

    Attributes:
        anime_id: Идентификатор аниме.
        status: Статус просмотра.
        current_episode: Текущая серия либо None.
        rating: Оценка пользователя либо None.
    """

    anime_id: int
    status: str
    current_episode: int | None = None
    rating: float | None = None


class ExportHighlightResponse(BaseModel):
    """Хайлайт автора в выгрузке данных.

    Attributes:
        id: Идентификатор хайлайта.
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        title: Название момента.
    """

    id: int
    anime_id: int
    episode: int
    title: str


class ExportCollectionResponse(BaseModel):
    """Коллекция автора в выгрузке данных.

    Attributes:
        id: Идентификатор коллекции.
        title: Название коллекции.
        is_public: Публична ли коллекция.
    """

    id: int
    title: str
    is_public: bool


class AccountExportResponse(BaseModel):
    """Машиночитаемая копия данных пользователя.

    Attributes:
        profile: Раздел профиля владельца.
        favorites: Избранные работы.
        statuses: Записи дневника просмотра.
        highlights: Созданные хайлайты.
        collections: Созданные коллекции.
    """

    profile: ExportProfileResponse
    favorites: list[ExportFavoriteResponse] = []
    statuses: list[ExportStatusResponse] = []
    highlights: list[ExportHighlightResponse] = []
    collections: list[ExportCollectionResponse] = []
