from __future__ import annotations

import pytest

from backend.infrastructure.external import WatchSourceProvider


def test_watch_source_provider_is_abstract():
    """Проверяем, что базовый контракт WatchSourceProvider нельзя инстанцировать напрямую."""
    with pytest.raises(TypeError):
        WatchSourceProvider()
