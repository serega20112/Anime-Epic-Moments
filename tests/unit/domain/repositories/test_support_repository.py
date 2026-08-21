from __future__ import annotations

from backend.application.interface.repositories.support_repository import SupportRepository


class TestSupportRepository:
    def test_abstract_method_names(self):
        assert {"add", "update"} <= set(SupportRepository.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            SupportRepository()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
