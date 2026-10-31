"""Добавление источника просмотра вручную."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AddWatchSourceCommand:
    """Команда создания озвучки и источника просмотра.

    Attributes:
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        translation_name: Название озвучки.
        translation_type: Тип озвучки.
        provider_name: Название внешнего провайдера.
        source_name: Название источника внутри провайдера.
        stream_url: Адрес потока.
        quality_label: Метка качества.
        language: Язык озвучки.
        source_type: Технический тип источника.
    """

    anime_id: int
    episode: int
    translation_name: str
    translation_type: str
    provider_name: str
    source_name: str
    stream_url: str
    quality_label: str
    language: str = "ru"
    source_type: str = "stream"
