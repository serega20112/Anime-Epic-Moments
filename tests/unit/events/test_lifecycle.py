from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.events import lifecycle


@pytest.mark.unit
class TestResolveLogLevel:
    async def test_known_level(self):
        assert await lifecycle._resolve_log_level("DEBUG") == logging.DEBUG

    async def test_unknown_level_defaults_to_info(self):
        assert await lifecycle._resolve_log_level("VERBOSE") == logging.INFO


@pytest.mark.unit
class TestLifespan:
    async def test_startup_initializes_logging_and_db(self, monkeypatch):
        setup_calls = []
        init_calls = []

        async def _setup_logging(**kwargs):
            setup_calls.append(kwargs)

        monkeypatch.setattr(lifecycle, "setup_logging", _setup_logging)
        monkeypatch.setattr(lifecycle, "init_db", _Recorder(init_calls))
        monkeypatch.setattr(lifecycle.Settings, "database_auto_init", True)

        app = FastAPI(lifespan=lifecycle.lifespan)
        with TestClient(app):
            pass

        assert len(setup_calls) == 1
        assert len(init_calls) == 1

    async def test_startup_skips_db_when_auto_init_disabled(self, monkeypatch):
        init_calls = []
        verify_calls = []

        async def _setup_logging(**kwargs):
            return None

        monkeypatch.setattr(lifecycle, "setup_logging", _setup_logging)
        monkeypatch.setattr(lifecycle, "init_db", _Recorder(init_calls))
        monkeypatch.setattr(lifecycle, "verify_schema", _Recorder(verify_calls))
        monkeypatch.setattr(lifecycle.Settings, "database_auto_init", False)

        app = FastAPI(lifespan=lifecycle.lifespan)
        with TestClient(app):
            pass

        assert init_calls == []
        assert len(verify_calls) == 1

    async def test_startup_fails_fast_on_missing_schema(self, monkeypatch):
        calls = []

        async def _setup_logging(**kwargs):
            return None

        monkeypatch.setattr(lifecycle, "setup_logging", _setup_logging)
        monkeypatch.setattr(lifecycle, "verify_schema", _Raise(RuntimeError("schema missing")))
        monkeypatch.setattr(lifecycle.Settings, "database_auto_init", False)

        app = FastAPI(lifespan=lifecycle.lifespan)
        with pytest.raises(RuntimeError, match="schema missing"):
            with TestClient(app):
                pass

        assert calls == []


class _Recorder:
    def __init__(self, calls: list) -> None:
        self.calls = calls

    async def __call__(self):
        self.calls.append(True)


class _Raise:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def __call__(self):
        raise self.error


@pytest.mark.unit
async def test_lifespan_module_importable():
    assert callable(lifecycle.lifespan)
