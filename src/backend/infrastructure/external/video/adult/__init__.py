"""18+ видео-источники: Hanime, Eporner, Hentaigasm.

Группа вынесена отдельно по смыслу контента, а не по способу включения: каждый
провайдер управляется собственным флагом (`HANIME_ENABLED`, `EPORNER_ENABLED`,
`HENTAIGASM_ENABLED`) и по умолчанию включён, как и остальные источники. Отдельного
зонтичного флага группы сознательно нет — он бы молча менял поведение привычных
окружений без на то запроса.

Формат ответов этих сервисов нестабилен, поэтому маппинг защищён от неожиданной
структуры и отбрасывает непригодные источники вместо падения всего поиска.
"""

from __future__ import annotations

from .eporner_provider import EpornerProvider
from .hanime_provider import HanimeProvider
from .hentaigasm_provider import HentaigasmProvider

__all__ = [
    "EpornerProvider",
    "HanimeProvider",
    "HentaigasmProvider",
]
