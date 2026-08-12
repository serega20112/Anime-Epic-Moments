from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.events import lifecycle


@pytest.mark.unit
class TestResolveLogLevel:
    def test_known_level(self):
        assert lifecycle._resolve_log_level("DEBUG") == logging.DEBUG

    def test_unknown_level_defaults_to_info(self):
        assert lifecycle._resolve_log_level("VERBOSE") == logging.INFO


@pytest.mark.unit
class TestRegisterLifecycleHandlers:
    def test_registers_startup_and_shutdown(self):
        app = FastAPI()
        lifecycle.register_lifecycle_handlers(app)

        assert len(app.router.on_startup) == 1
        assert len(app.router.on_shutdown) == 1

    def test_startup_initializes_logging_and_db(self, monkeypatch):
        setup_calls = []
        init_calls = []
        monkeypatch.setattr(lifecycle, "setup_logging", lambda **kwargs: setup_calls.append(kwargs))
        monkeypatch.setattr(lifecycle, "init_db", _init_db := _Recorder(init_calls))
        monkeypatch.setattr(lifecycle.Settings, "database_auto_init", True)

        app = FastAPI()
        lifecycle.register_lifecycle_handlers(app)
        with TestClient(app):
            pass

        assert len(setup_calls) == 1
        assert len(init_calls) == 1

    def test_startup_skips_db_when_auto_init_disabled(self, monkeypatch):
        init_calls = []
        monkeypatch.setattr(lifecycle, "setup_logging", lambda **kwargs: None)
        monkeypatch.setattr(lifecycle, "init_db", _Recorder(init_calls))
        monkeypatch.setattr(lifecycle.Settings, "database_auto_init", False)

        app = FastAPI()
        lifecycle.register_lifecycle_handlers(app)
        with TestClient(app):
            pass

        assert init_calls == []


class _Recorder:
    def __init__(self, calls: list) -> None:
        self.calls = calls

    async def __call__(self):
        self.calls.append(True)


@pytest.mark.unit
def test_lifecycle_module_importable():
    assert callable(lifecycle.register_lifecycle_handlers)