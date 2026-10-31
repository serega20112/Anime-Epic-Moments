"""Лексика поисковых запросов рекомендаций: стоп-слова, термы и окончания.

Словарь и разбор текста вынесены из самой политики скоринга: список служебных
слов занимает больше места, чем все правила оценки, и правится по совершенно
другим причинам — по жалобам на распознавание запросов.
"""

from __future__ import annotations

import re

from backend.domain.entities.anime.anime import Anime

STOP_WORDS = frozenset(
    {
        "a",
        "about",
        "all",
        "an",
        "and",
        "anime",
        "anim",
        "as",
        "at",
        "be",
        "but",
        "for",
        "from",
        "good",
        "hero",
        "i",
        "if",
        "in",
        "is",
        "it",
        "like",
        "more",
        "my",
        "no",
        "not",
        "of",
        "on",
        "or",
        "show",
        "similar",
        "something",
        "than",
        "that",
        "the",
        "this",
        "to",
        "want",
        "with",
        "без",
        "более",
        "бы",
        "в",
        "во",
        "вроде",
        "где",
        "для",
        "или",
        "как",
        "какое",
        "какой",
        "какую",
        "ли",
        "мне",
        "на",
        "не",
        "но",
        "ну",
        "о",
        "об",
        "под",
        "по",
        "пожалуйста",
        "посоветуй",
        "посоветуйте",
        "про",
        "с",
        "со",
        "только",
        "у",
        "хочу",
        "что",
        "что-то",
        "чтобы",
        "это",
        "этот",
        "эту",
        "аним",
    }
)
SUBJECT_PATTERNS = (
    re.compile(r"(?:^|\s)(?:про|about)\s+([^,.!?]+)", re.IGNORECASE),
    re.compile(r"(?:^|\s)(?:with|с)\s+([^,.!?]+)", re.IGNORECASE),
)
WORD_PATTERN = re.compile(r"[a-zA-Zа-яА-Я0-9-]+")
MIN_TERM_LENGTH = 3
TERM_SUFFIX_MIN_EXTRA = 2
TERM_SUFFIXES = (
    "ами",
    "ями",
    "ого",
    "ему",
    "ому",
    "ыми",
    "ими",
    "ах",
    "ях",
    "ов",
    "ев",
    "ей",
    "ам",
    "ям",
    "ом",
    "ем",
    "ой",
    "ий",
    "ый",
    "ая",
    "ое",
    "ые",
    "ть",
    "ти",
    "ing",
    "ers",
    "ies",
    "es",
    "ed",
    "er",
    "ly",
    "s",
    "а",
    "я",
    "ы",
    "и",
    "е",
    "у",
    "ю",
    "о",
)


def normalize_term(value: str) -> str:
    """Привести терм к нижнему регистру, отбросив одно из окончаний.

    Args:
        value: Исходный терм.

    Returns:
        str: Терм для сравнения запроса и карточки тайтла.
    """
    term = str(value or "").strip().lower()
    for suffix in TERM_SUFFIXES:
        if len(term) > len(suffix) + TERM_SUFFIX_MIN_EXTRA and term.endswith(suffix):
            return term[: -len(suffix)]
    return term


def extract_terms(value: str) -> list[str]:
    """Разбить текст на значимые термы без стоп-слов и повторов.

    Args:
        value: Произвольный текст запроса либо карточки тайтла.

    Returns:
        list[str]: Уникальные значимые термы в нижнем регистре.
    """
    normalized_terms: list[str] = []
    seen: set[str] = set()
    for raw_term in WORD_PATTERN.findall(str(value or "").lower()):
        term = normalize_term(raw_term)
        if len(term) < MIN_TERM_LENGTH or term in STOP_WORDS or term in seen:
            continue
        seen.add(term)
        normalized_terms.append(term)
    return normalized_terms


def extract_subject_terms(query: str) -> list[str]:
    """Выделить из запроса предмет поиска.

    Args:
        query: Нормализованный запрос пользователя.

    Returns:
        list[str]: Термы явной темы запроса.
    """
    subject_terms: list[str] = []
    for pattern in SUBJECT_PATTERNS:
        match = pattern.search(str(query or ""))
        if not match:
            continue
        subject_terms.extend(extract_terms(match.group(1)))
    return subject_terms


def anime_text(anime: Anime) -> str:
    """Собрать текст карточки тайтла для оценки совпадения термов.

    Args:
        anime: Карточка тайтла из каталога.

    Returns:
        str: Название, описание и жанры одним блоком текста.
    """
    return " ".join(
        [
            str(anime.title or ""),
            str(anime.description or ""),
            " ".join(anime.genres or []),
        ]
    )


def title_and_description(anime: Anime) -> str:
    """Собрать название и описание тайтла одним нижнерегистровым блоком.

    Жанры сюда не входят: они уже учтены отдельным весом, и иначе одно и то
    же слово засчитывалось бы в похожести дважды.

    Args:
        anime: Карточка тайтла из каталога.

    Returns:
        str: Строка «название описание» в нижнем регистре.
    """
    return f"{anime.title or ''} {anime.description or ''}".lower()
