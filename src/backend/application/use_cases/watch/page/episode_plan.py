"""План серий и озвучек для страницы просмотра.

Здесь только чистые правила: какие серии реально доступны, сколько их у каждой
озвучки, что показывать в списке выбора. Правила вынесены из сценария, потому
что их проверяют отдельно от похода во внешние провайдеры.
"""

from __future__ import annotations

from collections.abc import Iterable

from backend.domain.policies.watch_policy import canonicalize_translation_name
from backend.domain.value_objects.watch.page_data import TranslationEpisodeCount

MAX_SELECTABLE_EPISODE = 500


def format_timestamp(seconds: float) -> str:
    """Переводит секунды в метку ``ММ:СС``.

    Args:
        seconds: Позиция в секундах.

    Returns:
        str: Метка времени для карточки хайлайта.
    """
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minutes:02d}:{sec:02d}"


def available_episodes(availability, active_translation_name, sources) -> list[int] | None:
    """Возвращает реально доступные серии тайтла или None без данных.

    Приоритет — набор серий озвучки, выбранной в плеере: так «фантомные» серии
    чужих студий не показываются. Если выбранной озвучки в карте доступности
    нет, берётся объединение всех озвучек, иначе None (клиент покажет диапазон
    из метаданных каталога).

    Args:
        availability: Карта доступности серий по озвучкам.
        active_translation_name: Озвучка, выбранная в плеере.
        sources: Источники текущей серии (не используются в расчёте, но
            сохраняют сигнатуру вызывающей стороны).

    Returns:
        list[int] | None: Отсортированные доступные серии или None.
    """
    if availability and active_translation_name:
        canonical_active = canonicalize_translation_name(active_translation_name)
        for record in availability:
            if (
                canonicalize_translation_name(record.title) == canonical_active
                and record.available_episodes
            ):
                return sorted(set(record.available_episodes))
    if availability:
        merged = sorted({ep for record in availability for ep in record.available_episodes})
        if merged:
            return merged
    return None


def resolve_episode_total(
    available_episodes_list: list[int] | None,
    episode: int,
    fallback_total: int | None = None,
) -> int | None:
    """Считает общее число серий по фактически доступным.

    Приоритет — реальный набор серий от провайдера: так «фантомные» серии
    чужих озвучек не попадают в общий счёт. Если карты доступности нет,
    используется ``fallback_total`` из каталога.

    Args:
        available_episodes_list: Реально доступные серии либо None.
        episode: Текущая серия.
        fallback_total: Число серий из каталога.

    Returns:
        int | None: Максимум доступных серий либо fallback.
    """
    if available_episodes_list:
        return max(max(available_episodes_list), max(int(episode), 1))
    if fallback_total:
        return max(int(fallback_total), max(int(episode), 1))
    return max(int(episode), 1) if episode else None


def build_episode_options(
    total: int | None,
    current_episode: int,
    available_episodes_list: list[int] | None = None,
) -> list[int]:
    """Строит список номеров серий для выбора в плеере.

    Когда известен реальный набор серий, отдаются только они, чтобы не
    показывать невышедшие. Иначе используется диапазон ``1..total``, но не
    длиннее :data:`MAX_SELECTABLE_EPISODE`.

    Args:
        total: Общее число серий (fallback).
        current_episode: Текущая серия.
        available_episodes_list: Реально доступные серии или None.

    Returns:
        list[int]: Номера серий, доступные для выбора.
    """
    if available_episodes_list:
        capped = [
            ep
            for ep in sorted(set(available_episodes_list))
            if 1 <= int(ep) <= MAX_SELECTABLE_EPISODE
        ]
        if current_episode not in capped:
            capped.append(int(current_episode))
            capped.sort()
        return capped
    if total is None:
        return []
    capped_total = max(int(total), int(current_episode), 1)
    if capped_total > MAX_SELECTABLE_EPISODE:
        return []
    return list(range(1, capped_total + 1))


def build_translation_counts(
    availability,
    source_cards,
    translations,
    active_translation_name,
) -> list[TranslationEpisodeCount]:
    """Собирает счётчики вышедших серий по озвучкам для интерфейса.

    Счётчик берётся из ответа провайдера по каждой озвучке отдельно, а не из
    метаданных каталога: это исключает «12 серий» там, где студия выпустила 8.

    Args:
        availability: Карта доступности серий по озвучкам.
        source_cards: Источники, найденные для текущей серии.
        translations: Локальные дорожки тайтла по id.
        active_translation_name: Озвучка, выбранная в плеере.

    Returns:
        list[TranslationEpisodeCount]: Счётчики для отображения.
    """
    if not availability:
        return []
    counts: list[TranslationEpisodeCount] = []
    seen_names: set[str] = set()
    for record in availability:
        canonical = canonicalize_translation_name(record.title)
        if canonical in seen_names:
            continue
        seen_names.add(canonical)
        is_active = bool(
            active_translation_name
            and canonicalize_translation_name(active_translation_name) == canonical
        )
        counts.append(
            TranslationEpisodeCount(
                translation_name=record.title,
                available_count=int(record.episodes_count),
                is_active=is_active,
            )
        )
    return counts


def dedupe_by_quality(sources: Iterable) -> list:
    """Убирает точные дубли источников, оставляя разные релизы рядом.

    Ключ — тройка (озвучка, качество, источник). Без источника в ключе
    провайдеры без честной разметки качества схлопывали выдачу в один
    элемент: у Hentaigasm одна «озвучка» на весь сайт и качество ``auto`` у
    каждого ролика, поэтому из десяти найденных видео оставалось одно.
    Разные ``source_name`` — это разные ролики, и они должны быть видны все.

    Args:
        sources: Источники в порядке приоритета.

    Returns:
        list: Источники без точных дублей.
    """
    deduped: list = []
    seen: set[tuple[int, str, str]] = set()
    for item in sources:
        key = (
            int(item.translation_id),
            str(item.quality_label or "").strip().lower(),
            str(item.source_name or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
