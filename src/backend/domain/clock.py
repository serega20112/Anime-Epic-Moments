"""Единые часы приложения: все метки времени хранятся в naive UTC."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Вернуть текущий момент в UTC без смещения.

    Колонки дат в базе объявлены как ``timestamp without time zone``, поэтому в
    них сохраняется naive-время по UTC: aware-значение драйвер отклоняет, а
    ``datetime.utcnow()`` помечен устаревшим. Единственная точка, где выбирается
    этот компромисс, — функция :func:`utc_now`.

    Returns:
        datetime: Текущий момент в UTC без tzinfo.
    """
    return datetime.now(UTC).replace(tzinfo=None)
