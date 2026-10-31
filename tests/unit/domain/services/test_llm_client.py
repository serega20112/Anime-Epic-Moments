from __future__ import annotations

import inspect

from backend.application.interface.services.llm_client import LLMClientInterface
from backend.infrastructure.external.llm.failover_llm_client import FailoverLLMClient
from backend.infrastructure.external.llm.huggingface_llm_client import HuggingFaceLLMClient


class TestLLMClientInterface:
    """Тесты контракта порта клиента языковой модели."""

    def test_abstract_method_names(self):
        """Что тестируем: порт обещает ровно то, что модели умеют.
        Что передаём: набор абстрактных методов порта.
        Что ожидаем: построение поисковых запросов и описание вкусов; поиска
        тайтлов по описанию здесь нет — его выполняет каталог аниме.
        """
        assert {"build_search_queries_with_meta", "describe_taste_profile"} == set(
            LLMClientInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        """Что тестируем: порт нельзя создать напрямую.
        Что передаём: попытку инстанцировать абстрактный класс.
        Что ожидаем: TypeError.
        """
        try:
            LLMClientInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True

    def test_implementations_cover_every_port_method(self):
        """Что тестируем: оба клиента закрывают порт без пропущенных методов.
        Что передаём: клиента Hugging Face и клиент с переключением провайдеров.
        Что ожидаем: каждый абстрактный метод присутствует с тем же списком
        параметров — иначе подмена провайдера упадёт в рантайме.
        """
        for client in (HuggingFaceLLMClient, FailoverLLMClient):
            for method_name in LLMClientInterface.__abstractmethods__:
                port_method = getattr(LLMClientInterface, method_name)
                implementation = getattr(client, method_name, None)
                assert implementation is not None, f"{client.__name__}.{method_name}"
                assert list(inspect.signature(port_method).parameters) == list(
                    inspect.signature(implementation).parameters
                )
