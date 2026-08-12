from __future__ import annotations

import pytest

from backend.infrastructure.di.dishka_container import build_dishka_container


@pytest.mark.unit
class TestBuildDishkaContainer:
    def test_returns_async_container(self):
        container = build_dishka_container()

        assert container is not None

    def test_returns_distinct_containers_per_call(self):
        first = build_dishka_container()
        second = build_dishka_container()

        assert first is not second