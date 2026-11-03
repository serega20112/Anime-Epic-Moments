"""Карточка тайтла для мобильного клиента: серии с прогрессом.

Страница просмотра уже содержит карточку, источники, статус, оценку и позицию
текущей серии. Здесь добавляется лишь то, чего в странице нет: отметка
«в избранном» и по-серийный прогресс, собранный из дневника зрителя.
"""

from dataclasses import dataclass, field

from backend.domain.value_objects.watch.page_data import WatchPageData


@dataclass(frozen=True)
class EpisodeProgress:
    """Одна серия тайтла с признаком просмотра и позицией продолжения.

    Attributes:
        number: Номер серии.
        title: Название серии либо None, когда каталог его не отдаёт.
        duration_seconds: Длительность серии либо None, когда неизвестна.
        watched: Просмотрена ли серия по текущей позиции дневника зрителя.
        position_seconds: Сохранённая позиция для продолжения просмотра.
    """

    number: int
    title: str | None = None
    duration_seconds: int | None = None
    watched: bool = False
    position_seconds: float = 0.0


@dataclass(frozen=True)
class AnimeDetail:
    """Карточка тайтла с по-серийным прогрессом и признаком избранного.

    Attributes:
        page: Данные страницы просмотра (карточка, источники, статус, позиция).
        favorites: В избранном ли тайтл у зрителя.
        episodes: Прогресс по доступным сериям тайтла.
    """

    page: WatchPageData
    favorites: bool
    episodes: list[EpisodeProgress] = field(default_factory=list)
