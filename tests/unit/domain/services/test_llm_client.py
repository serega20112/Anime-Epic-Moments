from __future__ import annotations

from backend.domain.services.llm_client import LLMClientInterface


class TestLLMClientInterface:
    def test_abstract_method_names(self):
        assert {"describe_taste_profile", "search_by_description"} <= set(
            LLMClientInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            LLMClientInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
