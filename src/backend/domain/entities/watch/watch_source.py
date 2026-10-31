"""Сущность источника просмотра."""

from datetime import datetime

from backend.domain.clock import utc_now

MIN_EPISODE = 1


class WatchSource:
    """Источник видео: провайдер, озвучка и плеер серии.

    Имена провайдера и источника приходят из внешних парсеров и участвуют в
    дедупликации и удалении протухших ссылок, поэтому нормализуются сразу при
    создании: сравнение «Kodik » и «kodik» не должно плодить дубли в базе.
    """

    def __init__(
        self,
        anime_id: int,
        episode: int,
        translation_id: int,
        provider_name: str,
        source_name: str,
        stream_url: str,
        quality_label: str,
        source_type: str = "stream",
        id: int | None = None,
        created_at: datetime | None = None,
    ):
        """Создать источник просмотра, приведя поля к каноническому виду.

        Args:
            anime_id: Идентификатор тайтла.
            episode: Номер серии; значения меньше первой поднимаются до первой.
            translation_id: Идентификатор озвучки.
            provider_name: Имя провайдера без обрамляющих пробелов.
            source_name: Имя источника внутри провайдера.
            stream_url: Ссылка на поток или файл воспроизведения.
            quality_label: Метка качества.
            source_type: Тип источника (stream, embed, external, download).
            id: Идентификатор записи в хранилище.
            created_at: Момент появления записи.
        """
        self.id = id
        self.anime_id = anime_id
        self.episode = max(MIN_EPISODE, int(episode))
        self.translation_id = translation_id
        self.provider_name = str(provider_name or "").strip()
        self.source_name = str(source_name or "").strip()
        self.stream_url = stream_url
        self.quality_label = quality_label
        self.source_type = str(source_type or "stream").strip()
        self.created_at = created_at or utc_now()
