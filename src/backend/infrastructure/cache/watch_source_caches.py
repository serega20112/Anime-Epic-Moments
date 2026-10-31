"""Кэши сервиса синхронизации источников просмотра.

Сервис собирается в DI со scope=REQUEST, то есть заново на каждый HTTP-запрос,
поэтому его кэши не могут жить в инстансе: заявленные 10 и 30 минут TTL никогда
бы не наступили, а каждый заход на страницу просмотра снова обращался бы к
внешним сайтам (Hentaigasm и Eporner — по 2–4 секунды на запрос). Holder
создаётся один раз в scope=APP и разделяется всеми запросами процесса, а
приложение знает о нём только через порт :class:`TTLCacheInterface`.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.domain.value_objects.watch.translation_availability import (
    TranslationEpisodeAvailability,
)
from backend.infrastructure.cache.ttl_cache import TTLCache

EMPTY_RESULT_TTL_SECONDS = 600
EMPTY_RESULT_MAX_ENTRIES = 512
AVAILABILITY_TTL_SECONDS = 1800
AVAILABILITY_MAX_ENTRIES = 256


@dataclass(frozen=True, slots=True)
class WatchSourceCaches:
    """Пара процесс-глобальных кэшей для сервиса синхронизации источников.

    Attributes:
        empty_results: Отметки «у тайтла нет источников», чтобы не опрашивать
            провайдеров повторно в пределах TTL.
        availability: Карта доступности серий по озвучкам.
    """

    empty_results: TTLCache[object, bool]
    availability: TTLCache[object, list[TranslationEpisodeAvailability]]

    @classmethod
    def create(cls) -> WatchSourceCaches:
        """Построить кэши с настроенными TTL и лимитами записей.

        Returns:
            WatchSourceCaches: Готовые к использованию кэши.
        """
        return cls(
            empty_results=TTLCache(
                ttl_seconds=EMPTY_RESULT_TTL_SECONDS, max_entries=EMPTY_RESULT_MAX_ENTRIES
            ),
            availability=TTLCache(
                ttl_seconds=AVAILABILITY_TTL_SECONDS,
                max_entries=AVAILABILITY_MAX_ENTRIES,
            ),
        )
