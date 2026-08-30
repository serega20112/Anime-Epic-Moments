from dataclasses import dataclass, field


@dataclass
class TranslationEpisodeAvailability:
    """Доступность серий у конкретной озвучки одного тайтла.

    Строится строго по ответу провайдера: счётчик и список серий принадлежат
    только этой озвучке и не наследуются от других переводов или метаданных
    каталога — это исключает «фантомные» серии у студий с неполным релизом.

    Attributes:
        translation_id: Внешний id озвучки у провайдера.
        title: Название озвучки (студии).
        translation_type: Тип дорожки (voice/sub).
        episodes_count: Сколько серий фактически доступно у этой озвучки.
        available_episodes: Отсортированный список доступных номеров серий.
        link: Ссылка на материал озвучки (плеер/сериал), если есть.
    """

    translation_id: int
    title: str
    translation_type: str
    episodes_count: int
    available_episodes: list[int] = field(default_factory=list)
    link: str | None = None

    def has_episode(self, episode: int) -> bool:
        """Проверяет, доступна ли серия у этой озвучки.

        Args:
            episode: Номер серии.

        Returns:
            bool: True, если серия есть в available_episodes.
        """
        return int(episode) in self.available_episodes
