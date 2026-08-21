from __future__ import annotations

from backend.application.interface.services.ttl_cache import TTLCacheInterface


class TestTTLCacheInterface:
    def test_abstract_method_names(self):
        assert {"get", "set", "delete", "close"} <= set(TTLCacheInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            TTLCacheInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
