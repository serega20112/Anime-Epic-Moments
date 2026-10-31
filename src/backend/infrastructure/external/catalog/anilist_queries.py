"""Сборка GraphQL-запросов к AniList.

AniList принимает только GraphQL, поэтому запросы — это данные: поля выборки,
объявления переменных и аргументы фильтра. Держим их отдельно от клиента,
чтобы клиент читался как транспорт, а не как склейка многострочных строк.
"""

from __future__ import annotations

from collections.abc import Sequence

ANILIST_BASE_URL = "https://graphql.anilist.co"

ANILIST_GENRES = {
    "Action",
    "Adventure",
    "Comedy",
    "Drama",
    "Ecchi",
    "Fantasy",
    "Hentai",
    "Horror",
    "Mahou Shoujo",
    "Mecha",
    "Music",
    "Mystery",
    "Psychological",
    "Romance",
    "Sci-Fi",
    "Slice of Life",
    "Sports",
    "Supernatural",
    "Thriller",
}

_SEARCH_FIELDS = """
                  id
                  idMal
                  episodes
                  title { romaji english native }
                  description
                  genres
                  isAdult
                  seasonYear
                  averageScore
                  coverImage { large }
"""

_SEASON_FIELDS = """
              id
              title { romaji english native }
              seasonYear
              coverImage { large }
"""

_CATALOG_FIELDS = """
                      id
                      idMal
                      episodes
                      title { romaji english native }
                      description
                      genres
                      seasonYear
                      averageScore
                      coverImage { large }
"""

_FORMAT_MAP = {
    "tv": "TV",
    "movie": "MOVIE",
    "ova": "OVA",
    "ona": "ONA",
    "special": "SPECIAL",
}

_STATUS_MAP = {
    "airing": "RELEASING",
    "complete": "FINISHED",
    "upcoming": "NOT_YET_RELEASED",
}

_SORT_MAP = {
    "rating": {"desc": "SCORE_DESC", "asc": "SCORE"},
    "popularity": {"desc": "POPULARITY_DESC", "asc": "POPULARITY"},
    "newest": {"desc": "START_DATE_DESC", "asc": "START_DATE"},
    "title": {"desc": "TITLE_ROMAJI_DESC", "asc": "TITLE_ROMAJI"},
}


def search_query(include_adult: bool) -> str:
    """Собрать запрос поиска тайтлов по строке.

    Запрос используется и для поиска по названию, и для поиска по описанию:
    AniList не различает эти режимы, разница только в строке запроса.

    Args:
        include_adult: Разрешать ли взрослые тайтлы в выдаче.

    Returns:
        str: GraphQL-запрос страницы поиска.
    """
    adult_filter = "" if include_adult else ", isAdult: false"
    return f"""
            query ($search: String, $perPage: Int) {{
              Page(perPage: $perPage) {{
                media(search: $search, type: ANIME{adult_filter}) {{{_SEARCH_FIELDS}                }}
              }}
            }}
            """


def media_query(declarations: str, media_expression: str) -> str:
    """Собрать запрос одного тайтла по идентификатору.

    Args:
        declarations: Объявления переменных GraphQL без круглых скобок.
        media_expression: Выражение поля ``media`` (``Media(id: $id, ...)``).

    Returns:
        str: GraphQL-запрос одного тайтла.
    """
    return f"""
        query ({declarations}) {{
          media: {media_expression} {{{_SEARCH_FIELDS}          }}
        }}
        """


def season_popular_query() -> str:
    """Вернуть запрос популярных тайтлов сезона.

    Returns:
        str: GraphQL-запрос сезонной подборки.
    """
    return f"""
        query ($season: MediaSeason, $year: Int, $perPage: Int) {{
          Page(perPage: $perPage) {{
            media(
              season: $season
              seasonYear: $year
              type: ANIME
              sort: SCORE_DESC
            ) {{{_SEASON_FIELDS}            }}
          }}
        }}
        """


def split_genres(genres: Sequence[str]) -> tuple[list[str], list[str]]:
    """Разделить запрошенные фильтры на жанры AniList и свободные теги.

    AniList фильтрует жанры аргументом ``genre_in``, а остальные названия —
    ``tag_in``; списки не пересекаются, иначе один и тот же фильтр ушёл бы
    дважды.

    Args:
        genres: Запрошенные жанры и теги.

    Returns:
        tuple[list[str], list[str]]: Жанры и теги в порядке запроса.
    """
    selected = [str(name).strip() for name in genres if str(name).strip()]
    return (
        [name for name in selected if name in ANILIST_GENRES],
        [name for name in selected if name not in ANILIST_GENRES],
    )


def catalog_query(
    *,
    genres: Sequence[str],
    tags: Sequence[str],
    include_genres: bool,
    include_tags: bool,
    media_type: str,
    status: str,
    year_from: int | None,
    year_to: int | None,
    min_score: float | None,
    sort: str,
    order: str,
    page: int,
    per_page: int,
) -> tuple[str, dict[str, object]]:
    """Собрать запрос каталога и переменные к нему.

    Args:
        genres: Жанры AniList, которые нужно применить.
        tags: Свободные теги, которые нужно применить.
        include_genres: Добавлять ли фильтр по жанрам.
        include_tags: Добавлять ли фильтр по тегам.
        media_type: Нормализованный формат тайтла.
        status: Нормализованный статус выхода.
        year_from: Нижняя граница года выпуска.
        year_to: Верхняя граница года выпуска.
        min_score: Минимальный рейтинг в шкале 0–10.
        sort: Ключ сортировки.
        order: Направление сортировки.
        page: Номер страницы, начиная с единицы.
        per_page: Размер страницы.

    Returns:
        tuple[str, dict[str, object]]: GraphQL-запрос и переменные.
    """
    normalized_type = str(media_type).strip().lower()
    normalized_status = str(status).strip().lower()
    direction = "asc" if str(order).strip().lower() == "asc" else "desc"

    args = ["type: ANIME", f"sort: {_SORT_MAP.get(sort, {}).get(direction, 'SCORE_DESC')}"]
    declarations = ["$perPage: Int", "$page: Int"]
    variables: dict[str, object] = {"perPage": int(per_page), "page": int(page)}

    if normalized_type in _FORMAT_MAP:
        args.append("format: $format")
        declarations.append("$format: MediaFormat")
        variables["format"] = _FORMAT_MAP[normalized_type]

    if normalized_status in _STATUS_MAP:
        args.append("status: $status")
        declarations.append("$status: MediaStatus")
        variables["status"] = _STATUS_MAP[normalized_status]

    if isinstance(year_from, int):
        args.append("startDate_greater: $yearGreater")
        declarations.append("$yearGreater: FuzzyDateInt")
        variables["yearGreater"] = int(f"{year_from - 1}1231")
    if isinstance(year_to, int):
        args.append("startDate_lesser: $yearLess")
        declarations.append("$yearLess: FuzzyDateInt")
        variables["yearLess"] = int(f"{year_to}1231")
    if isinstance(min_score, (int, float)) and 0 <= float(min_score) <= 10:
        args.append("averageScore_greater: $minScore")
        declarations.append("$minScore: Int")
        variables["minScore"] = int(float(min_score) * 10)

    if include_genres and genres:
        args.append("genre_in: $genre")
        declarations.append("$genre: [String]")
        variables["genre"] = list(genres)
    if include_tags and tags:
        args.append("tag_in: $tag")
        declarations.append("$tag: [String]")
        variables["tag"] = list(tags)

    query = f"""
                query ({", ".join(declarations)}) {{
                  Page(page: $page, perPage: $perPage) {{
                    pageInfo {{ total }}
                    media({" ".join(args)}) {{{_CATALOG_FIELDS}                    }}
                  }}
                }}
                """
    return query, variables
