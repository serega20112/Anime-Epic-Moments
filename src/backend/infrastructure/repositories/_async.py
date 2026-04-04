from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any


def repository_method(method: Callable[..., Any]):
    """Run legacy sync ORM code inside AsyncSession.run_sync."""

    @wraps(method)
    async def wrapped(self, *args, **kwargs):
        async_session = self.session

        def runner(sync_session):
            original_session = self.session
            self.session = sync_session
            try:
                return method(self, *args, **kwargs)
            finally:
                self.session = original_session

        if not hasattr(async_session, "run_sync"):
            return runner(async_session)
        return await async_session.run_sync(runner)

    return wrapped
