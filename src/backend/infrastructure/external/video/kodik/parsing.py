"""Разбор ответов Kodik: релевантность тайтла, эпизоды, ссылки и нормализация.

Модуль не выполняет сетевые запросы: он превращает уже полученный JSON в ссылки и
признаки совпадения. Правила сопоставления названий живут здесь же — в константах
``_TITLE_ALIASES`` и ``_MAX_EXTRA_CANDIDATE_WORDS``.
"""

import asyncio
import base64
import re

_LINKS_CONCURRENCY = 8

_TITLE_ALIASES: dict[str, str] = {
    "блич": "bleach",
}
_MAX_EXTRA_CANDIDATE_WORDS = 3


class KodikParsingMixin:
    """Разбор ответов Kodik: релевантность тайтла, эпизоды, ссылки и нормализация.

    Методы работают с состоянием смешивающего класса (`self.session`, настройки
    `self.api_url`) и сами сетевых запросов не выполняют.
    """

    async def _collect_video_links(
        self, materials: list[dict], episode: int
    ) -> list[dict[str, list[dict[str, str]]]]:
        """Извлекает ссылки качества для всех материалов с ограничением параллелизма."""
        semaphore = asyncio.Semaphore(_LINKS_CONCURRENCY)

        async def fetch(material: dict) -> dict[str, list[dict[str, str]]]:
            """Собрать качества одного материала под общим семафором.

            Args:
                material: Сырой материал Kodik.

            Returns:
                dict[str, list[dict[str, str]]]: Качество → источники; пустой
                словарь, если у материала нет ссылки на серию.
            """
            material_link = await self._extract_episode_link(material=material, episode=episode)
            if not material_link:
                return {}
            async with semaphore:
                return await self._get_video_links(str(material_link))

        return list(await asyncio.gather(*(fetch(material) for material in materials)))

    async def _looks_relevant(
        self,
        material: dict,
        requested_title: str,
        requested_year: int | None,
    ) -> bool:
        """Проверяет, что материал Kodik относится к запрошенному тайтлу.

        Отсев идёт по году (допуск в один год — каталоги расходятся в дате
        релиза) и по названию: перебираются все варианты названия материала,
        каждый нормализуется и сопоставляется строго, без нечёткого сходства.

        Args:
            material: Сырой материал из выдачи Kodik.
            requested_title: Название, которое ищет пользователь.
            requested_year: Год тайтла либо None, если он неизвестен.

        Returns:
            bool: True, если материал признан относящимся к запрошенному тайтлу.
        """
        material_year = material.get("year")
        if (
            requested_year
            and isinstance(material_year, int)
            and abs(material_year - requested_year) > 1
        ):
            return False

        normalized_requested = await self._normalize_title(requested_title)
        if not normalized_requested:
            return False
        candidates = [
            material.get("title"),
            material.get("title_orig"),
            material.get("other_title"),
        ]
        material_data = material.get("material_data") or {}
        candidates.extend(
            [
                material_data.get("title"),
                material_data.get("anime_title"),
                material_data.get("title_en"),
            ]
        )
        for candidate in candidates:
            normalized_candidate = await self._normalize_title(candidate)
            if not normalized_candidate:
                continue
            if self._titles_match(normalized_requested, normalized_candidate):
                return True

        return False

    @staticmethod
    def _titles_match(requested: str, candidate: str) -> bool:
        """Строго сопоставляет нормализованные названия запрошенного тайтла и кандидата.

        Совпадением считается точное равенство либо случай, когда запрошенный
        тайтл целиком (по словам) содержится в названии кандидата без
        значительного «хвоста» из посторонних слов. Нечёткое сходство строк
        сознательно не используется: оно пропускает материалы других тайтлов.
        """
        if requested == candidate:
            return True
        requested_words = set(requested.split())
        candidate_words = set(candidate.split())
        if not requested_words:
            return False
        if requested_words <= candidate_words:
            return len(candidate_words) - len(requested_words) <= _MAX_EXTRA_CANDIDATE_WORDS
        return False

    async def _has_token_overlap(self, material: dict, requested_title: str) -> bool:
        """Проверяет непустое пересечение слов названий.

        Мягкий guard для id-пинной выдачи (:meth:`get_translations_availability`):
        отбрасывает материалы с чужим названием (пересечения токенов нет),
        не отбраковывая легитимные вариации названия одного тайтла.
        """
        normalized_requested = await self._normalize_title(requested_title)
        if not normalized_requested:
            return False
        requested_words = set(normalized_requested.split())
        if not requested_words:
            return False
        candidates = [
            material.get("title"),
            material.get("title_orig"),
            material.get("other_title"),
        ]
        material_data = material.get("material_data") or {}
        candidates.extend(
            [
                material_data.get("title"),
                material_data.get("anime_title"),
                material_data.get("title_en"),
            ]
        )
        for candidate in candidates:
            normalized_candidate = await self._normalize_title(candidate)
            if not normalized_candidate:
                continue
            if requested_words & set(normalized_candidate.split()):
                return True
        return False

    async def _extract_episode_link(self, material: dict, episode: int) -> str | None:
        """Достаёт ссылку серии из структуры сезонов материала.

        Сезон из `last_season` пробуется первым: у длинных тайтлов остальные
        сезоны содержат серии с тем же номером, но не те, что нужны.

        Args:
            material: Сырой материал Kodik.
            episode: Номер серии.

        Returns:
            str | None: Ссылка на серию либо None, если серии в материале нет.
        """
        seasons = material.get("seasons") or {}
        if not isinstance(seasons, dict) or not seasons:
            return await self._extract_single_part_link(material, episode)

        preferred_keys: list[str] = []
        last_season = material.get("last_season")
        if last_season is not None:
            preferred_keys.append(str(last_season))
        preferred_keys.extend(
            sorted(
                seasons.keys(), key=lambda value: (int(value) if value.isdigit() else 10**9, value)
            )
        )

        for season_key in preferred_keys:
            season = seasons.get(season_key)
            if not isinstance(season, dict):
                continue
            episodes = season.get("episodes") or {}
            if not isinstance(episodes, dict):
                continue
            raw_episode = episodes.get(str(episode)) or episodes.get(episode)
            if isinstance(raw_episode, str):
                return raw_episode
            if isinstance(raw_episode, dict):
                return raw_episode.get("link")
        return None

    async def _extract_single_part_link(self, material: dict, episode: int) -> str | None:
        """Достаёт ссылку из материала без ``seasons`` (фильм/OVA/спешкал).

        Kodik отдаёт одиночные материалы без структуры сезонов: ссылка лежит
        в верхнеуровневом поле ``link`` и принадлежит конкретному материалу,
        а не серии. Такой материал — это одна серия, поэтому ссылка валидна
        только для первой серии; для остальных возвращается None, чтобы
        страница не подменяла серию фильмом.

        Args:
            material: Материал Kodik без ``seasons``.
            episode: Запрошенный номер серии.

        Returns:
            str | None: Ссылка на материал для первой серии, иначе None.
        """
        if int(episode) != 1:
            return None
        link = await self._normalize_link(material.get("link"))
        if not link:
            return None
        parsed = await self._parse_link(link)
        if not parsed or parsed["type"] in {"serial", "seria", "season"}:
            return None
        return link

    async def _parse_link(self, link: str) -> dict[str, str] | None:
        """Разбирает ссылку Kodik на хост, тип, id материала, хэш и качество.

        Args:
            link: Ссылка вида `https://kodik.info/serial/123/abc/720p`.

        Returns:
            dict[str, str] | None: Компоненты ссылки либо None при несоответствии.
        """
        match = self._link_pattern.match(link)
        if not match:
            return None
        return {
            "host": match.group("host"),
            "type": match.group("kind"),
            "id": match.group("material_id"),
            "hash": match.group("hash"),
            "quality": match.group("quality"),
        }

    async def _decode_kodik_src(self, encoded_src: str) -> str | None:
        """Распаковывает «обфусцированный» src плеера Kodik в реальный URL.

        Kodik отдаёт адрес зашифрованным ROT-18 по латинице и без `=` на конце;
        здесь алфавитный сдвиг разворачивается обратно и достраивается паддинг.

        Args:
            encoded_src: Значение `src` из ответа плеера.

        Returns:
            str | None: Раскодированный URL либо None, если содержимое не base64.
        """
        shifted = []
        for char in encoded_src:
            if "A" <= char <= "Z":
                code = ord(char) + 18
                if code > ord("Z"):
                    code -= 26
                shifted.append(chr(code))
                continue
            if "a" <= char <= "z":
                code = ord(char) + 18
                if code > ord("z"):
                    code -= 26
                shifted.append(chr(code))
                continue
            shifted.append(char)

        try:
            shifted_text = "".join(shifted)
            padding = (-len(shifted_text)) % 4
            return base64.b64decode(shifted_text + "=" * padding).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    async def _normalize_link(self, value: str | None) -> str | None:
        """Приводит ссылку плеера к абсолютному HTTPS-виду.

        Kodik отдаёт относительные и протокол-независимые (`//host/path`) адреса;
        плееру нужен полный URL, иначе сегменты не загрузятся по HTTPS.

        Args:
            value: Исходное значение ссылки.

        Returns:
            str | None: Абсолютная ссылка либо None для пустого входа.
        """
        if not value:
            return None
        text = str(value).strip()
        if text.startswith("//"):
            return f"https:{text}"
        if text.startswith("/"):
            return f"https://kodikplayer.com{text}"
        return text

    async def _normalize_title(self, title: str | None) -> str:
        """Нормализует название для сопоставления: регистр, разделители и алиасы.

        Args:
            title: Название в любом написании.

        Returns:
            str: Приведённое название; пустая строка, если входа нет.
        """
        text = str(title or "").lower().strip()
        text = re.sub(r"[^a-zа-я0-9]+", " ", text, flags=re.IGNORECASE)
        text = " ".join(text.split())
        return _TITLE_ALIASES.get(text, text)

    async def _map_translation_type(self, value: str) -> str:
        """Переводит тип перевода Kodik в доменное значение.

        Args:
            value: Тип перевода из ответа провайдера.

        Returns:
            str: `sub`, `voice` либо исходное значение в нижнем регистре.
        """
        lowered = value.lower()
        if lowered == "subtitles":
            return "sub"
        return lowered or "voice"
