"""Политики приложения, собираемые из настроек для application-слоя."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.policies import (
    ApiFeatureFlags,
    AppReleaseInfo,
    CatalogLimitsPolicy,
    CookiePolicy,
    PasswordResetPolicy,
    ProxyTrustPolicy,
    RequestPolicy,
)
from backend.config import Settings
from backend.domain.policies.anime_safety_policy import AnimeSafetyPolicy


class PolicyProvidersMixin(Provider):
    """Политики приложения, собираемые из настроек для application-слоя.

    Часть провайдера: методы `@provide` собираются dishka из базовых
    классов, поэтому mixin самодостаточен и наследует `Provider`.
    """

    @provide(scope=Scope.APP)
    async def password_reset_policy(self) -> PasswordResetPolicy:
        """Дать узкую политику сброса пароля из конфигурации.

        Returns:
            PasswordResetPolicy: Адрес приложения и срок жизни токена сброса.
        """
        return PasswordResetPolicy(
            base_url=Settings.app_base_url,
            expire_minutes=Settings.password_reset_expire_minutes,
        )

    @provide(scope=Scope.APP)
    async def cookie_policy(self) -> CookiePolicy:
        """Дать политику cookie из конфигурации.

        Returns:
            CookiePolicy: Флаги cookie и сроки жизни токенов.
        """
        return CookiePolicy(
            secure=Settings.cookie_secure,
            samesite=Settings.cookie_samesite,
            domain=Settings.cookie_domain,
            access_expire_minutes=Settings.access_token_expire_minutes,
            refresh_expire_days=Settings.refresh_token_expire_days,
        )

    @provide(scope=Scope.APP)
    async def request_policy(self) -> RequestPolicy:
        """Дать политику HTTP-запросов.

        Returns:
            RequestPolicy: Лимит тела, разрешённые origin и параметры HSTS.
        """
        return RequestPolicy(
            max_request_bytes=Settings.max_request_bytes,
            base_url=Settings.app_base_url,
            allowed_origins=tuple(Settings.app_allowed_origins),
            hsts_max_age=Settings.hsts_max_age,
            cookie_secure=Settings.cookie_secure,
        )

    @provide(scope=Scope.APP)
    async def proxy_trust_policy(self) -> ProxyTrustPolicy:
        """Дать политику доверенных прокси.

        Returns:
            ProxyTrustPolicy: Адреса и сети прокси, которым верится в X-Forwarded-For.
        """
        return ProxyTrustPolicy(trusted_proxies=tuple(Settings.trusted_proxies))

    @provide(scope=Scope.APP)
    async def anime_safety_policy(self) -> AnimeSafetyPolicy:
        """Дать доменную политику возрастной безопасности каталога.

        Returns:
            AnimeSafetyPolicy: Политика без параметров конфигурации.
        """
        return AnimeSafetyPolicy()

    @provide(scope=Scope.APP)
    async def catalog_limits_policy(self) -> CatalogLimitsPolicy:
        """Дать политику лимитов каталога и поиска.

        Returns:
            CatalogLimitsPolicy: Лимиты страниц и длин строк запросов каталога.
        """
        return CatalogLimitsPolicy(
            query_limit_max=Settings.anime_query_limit_max,
            autocomplete_limit_max=Settings.anime_autocomplete_limit_max,
            title_max_length=Settings.anime_title_max_length,
            description_max_length=Settings.anime_description_max_length,
            genre_hint_max_length=Settings.anime_genre_hint_max_length,
        )

    @provide(scope=Scope.APP)
    async def api_feature_flags(self) -> ApiFeatureFlags:
        """Дать набор фиче-флагов, о которых спрашивает клиент JSON API.

        Возвращённые значения выводятся из конфигурации: взрослая аудитория
        доступна, если включён хотя бы один взрослый провайдер источников.

        Returns:
            ApiFeatureFlags: Разрешения на взрослый контент и ручное добавление источников.
        """
        return ApiFeatureFlags(
            adult_sources_enabled=(
                Settings.hanime_enabled or Settings.eporner_enabled or Settings.hentaigasm_enabled
            ),
            manual_source_creation_enabled=Settings.feature_manual_source_creation,
        )

    @provide(scope=Scope.APP)
    async def app_release_info(self) -> AppReleaseInfo:
        """Дать сведения о релизе мобильного приложения из конфигурации.

        Значения берутся из переменных окружения окружения сборки и не зависят
        от запроса, поэтому провайдер живёт в скоупе приложения.

        Returns:
            AppReleaseInfo: Версии, адрес пакета и режим обслуживания.
        """
        return AppReleaseInfo(
            latest_app_version=Settings.mobile_latest_app_version,
            min_app_version=Settings.mobile_min_app_version,
            apk_url=Settings.mobile_apk_url,
            apk_sha256=Settings.mobile_apk_sha256,
            changelog_url=Settings.mobile_changelog_url,
            maintenance_mode=Settings.mobile_maintenance_mode,
        )
