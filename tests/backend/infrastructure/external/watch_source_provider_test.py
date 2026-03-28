from __future__ import annotations

import pytest

from src.backend.infrastructure.external.watch_source_provider import WatchSourceProvider


def test_watch_source_provider_is_abstract():
    """Проверяем, что базовый контракт WatchSourceProvider нельзя инстанцировать напрямую."""
    with pytest.raises(TypeError):
        WatchSourceProvider()
