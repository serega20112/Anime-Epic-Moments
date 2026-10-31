"""Запрос публичной коллекции по ссылке."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetSharedCollectionQuery:
    """Запрос коллекции, открытой по ссылке общего доступа.

    Attributes:
        collection_id: Идентификатор коллекции.
    """

    collection_id: int
