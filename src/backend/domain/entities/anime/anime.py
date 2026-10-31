"""Сущность аниме как ссылка на внешний каталог."""

from collections.abc import Iterable

ADULT_GENRE_MARKERS: tuple[str, ...] = ("hentai", "ecchi", "adult", "эрот", "sex", "nsfw")


def has_adult_genres(genres: Iterable[str] | None) -> bool:
    """Проверяет, помечен ли список жанров как взрослый (18+) контент.

    Args:
        genres: Жанры тайтла либо None, если жанры неизвестны.

    Returns:
        bool: True для hentai/ecchi/adult-жанров.
    """
    joined = " ".join(genres or []).lower()
    return any(marker in joined for marker in ADULT_GENRE_MARKERS)


class Anime:
    """Сущность Anime как external reference.

    Не хранит обложки в БД, только URL.
    """

    def __init__(
        self,
        external_id: int | str,
        title: str,
        original_title: str | None = None,
        description: str | None = None,
        genres: list[str] | None = None,
        year: int | None = None,
        rating: float | None = None,
        cover_url: str | None = None,
        episode_count: int | None = None,
    ):
        """Создать аниме с заданными атрибутами каталога."""
        self.external_id = external_id
        self.title = title
        self.original_title = original_title
        self.description = description
        self.genres = genres or []
        self.year = year
        self.rating = rating
        self.cover_url = cover_url
        self.episode_count = episode_count

    def add_genre(self, genre: str):
        """Добавить жанр к аниме, если его ещё нет."""
        if genre not in self.genres:
            self.genres.append(genre)

    def remove_genre(self, genre: str):
        """Убрать жанр у аниме."""
        if genre in self.genres:
            self.genres.remove(genre)

    @property
    def mal_id(self) -> int | None:
        """Возвращает MAL/Shikimori идентификатор тайтла для строгой адресации.

        Номерной ``external_id`` означает адресацию в каталоге Shikimori/MAL.
        Нечисловые значения (например, AniList-id) не дают строгой адресации,
        поэтому возвращают None.

        Returns:
            int | None: MAL-id либо None, если ``external_id`` не число.
        """
        external_id = str(self.external_id or "").strip()
        if not external_id.isdigit():
            return None
        return int(external_id)

    @property
    def is_adult(self) -> bool:
        """Проверяет, относится ли тайтл ко взрослому (hentai) контенту.

        Returns:
            bool: True для hentai/ecchi/adult-жанров.
        """
        return has_adult_genres(self.genres)
