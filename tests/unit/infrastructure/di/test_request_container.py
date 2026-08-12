from __future__ import annotations

import pytest

from backend.infrastructure.di.request_container import RequestContainer
from backend.infrastructure.repositories.user_repository import UserRepository


class _FakeDishka:
    """Minimal AsyncContainer duck-type backed by a mapping."""

    def __init__(self, mapping):
        self._mapping = mapping

    async def get(self, dependency_type):
        if dependency_type not in self._mapping:
            raise KeyError(dependency_type)
        return self._mapping[dependency_type]


@pytest.fixture(autouse=True)
def _user_repo_sentinel():
    return object()


@pytest.fixture
def request_container(_user_repo_sentinel):
    fake = _FakeDishka({UserRepository: _user_repo_sentinel})
    return RequestContainer(fake)


async def test_get_delegates_to_dishka(request_container, _user_repo_sentinel):
    resolved = await request_container.get(UserRepository)
    assert resolved is _user_repo_sentinel


def test_unknown_dependency_raises(request_container):
    with pytest.raises(KeyError):
        import asyncio

        asyncio.run(request_container.get(str))


def test_user_repository_property_resolves(request_container, _user_repo_sentinel):
    assert request_container.user_repository is _user_repo_sentinel


def test_all_repository_properties_exist(request_container):
    for prop in (
        "user_repository",
        "highlight_repository",
        "favorite_repository",
        "collection_repository",
        "watch_repository",
        "support_repository",
        "jwt_service",
        "token_blocklist",
    ):
        assert hasattr(RequestContainer, prop)


def test_all_use_case_factories_exist():
    method_names = [
        name
        for name, member in RequestContainer.__dict__.items()
        if callable(member) and name.endswith("_use_case")
    ]
    assert len(method_names) >= 30