"""Модели запросов коллекций."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AddCollectionItemRequest(BaseModel):
    """Тело запроса добавления аниме в коллекцию.

    Клиент присылает только идентификатор аниме: снимок карточки сценарий
    собирает сам через каталог, а идентификатор пользователя берёт из сессии.

    Attributes:
        anime_id: Идентификатор добавляемого аниме.
    """

    model_config = ConfigDict(extra="ignore")

    anime_id: int = Field(gt=0)


class RemoveCollectionItemRequest(BaseModel):
    """Тело запроса удаления аниме из коллекции.

    Attributes:
        anime_id: Идентификатор удаляемого аниме.
    """

    model_config = ConfigDict(extra="ignore")

    anime_id: int = Field(gt=0)
