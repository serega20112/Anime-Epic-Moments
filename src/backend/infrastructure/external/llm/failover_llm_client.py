"""Клиент языковой модели с основным и резервным провайдерами."""

from __future__ import annotations

from backend.application.interface.services.llm_client import LLMClientInterface


class FailoverLLMClient(LLMClientInterface):
    """Обслуживает запросы к модели через основной провайдер с резервом.

    Поисковые запросы и описание вкусов сначала запрашиваются у основного
    провайдера, а при сбое повторяются у резервного.
    """

    def __init__(self, primary: LLMClientInterface, fallback: LLMClientInterface):
        """Создать клиент с основным и резервным провайдерами.

        Args:
            primary: Провайдер, опрашиваемый первым.
            fallback: Провайдер, к которому клиент переключается при сбое.
        """
        self.primary = primary
        self.fallback = fallback

    async def aclose(self) -> None:
        """Закрыть HTTP-клиенты обоих провайдеров."""
        for client in (self.primary, self.fallback):
            closer = getattr(client, "aclose", None)
            if closer is not None:
                await closer()

    async def build_search_queries_with_meta(
        self,
        description: str,
        genre_hint: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        age_rating: str = "all",
        allow_adult: bool = False,
    ) -> tuple[list[str], str, str | None]:
        """Собрать поисковые запросы через основной провайдер, повторяя у резервного."""
        if getattr(self.primary, "api_key", None):
            queries, mode, error = await self.primary.build_search_queries_with_meta(
                description=description,
                genre_hint=genre_hint,
                year_from=year_from,
                year_to=year_to,
                min_rating=min_rating,
                age_rating=age_rating,
                allow_adult=allow_adult,
            )
            if not mode.startswith("fallback"):
                return queries, mode, error
        return await self.fallback.build_search_queries_with_meta(
            description=description,
            genre_hint=genre_hint,
            year_from=year_from,
            year_to=year_to,
            min_rating=min_rating,
            age_rating=age_rating,
            allow_adult=allow_adult,
        )

    async def describe_taste_profile(self, profile_data: dict, fallback: str) -> str:
        """Описать вкусовой профиль через основной провайдер, повторяя у резервного."""
        primary_result = await self.primary.describe_taste_profile(profile_data, fallback)
        if primary_result != fallback:
            return primary_result
        return await self.fallback.describe_taste_profile(profile_data, fallback)
