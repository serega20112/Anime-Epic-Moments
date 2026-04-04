from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any


def external_method(method: Callable[..., Any]):
    """Expose blocking IO client methods as awaitable calls via a worker thread."""

    @wraps(method)
    async def wrapped(self, *args, **kwargs):
        return await asyncio.to_thread(method, self, *args, **kwargs)

    return wrapped
