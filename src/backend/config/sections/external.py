"""External service integration settings."""

from __future__ import annotations

import os

_PLACEHOLDER_PREFIXES = ("your-", "change-me", "xxx")


def _clean_secret(value: str | None) -> str | None:
    """Return the secret or None when it holds a placeholder stub.

    Args:
        value: Raw environment value.

    Returns:
        str | None: Cleaned value or None.
    """
    text = str(value or "").strip()
    if not text:
        return None
    lowered = text.lower()
    return None if lowered.startswith(_PLACEHOLDER_PREFIXES) else text


def hf_token() -> str | None:
    """Return the Hugging Face API token.

    Returns:
        str | None: Hugging Face token or None.
    """
    return os.getenv("HF_TOKEN")


def hf_provider() -> str | None:
    """Return the Hugging Face provider name.

    Returns:
        str | None: Provider name or None.
    """
    return os.getenv("HF_PROVIDER", "fireworks-ai")


def hf_model() -> str:
    """Return the Hugging Face model identifier.

    Returns:
        str: Model identifier.
    """
    return os.getenv("HF_MODEL", "openai/gpt-oss-120b")


def hf_api_url() -> str:
    """Return the Hugging Face chat completions URL.

    Returns:
        str: Chat completions URL.
    """
    return os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")


def openrouter_api_key() -> str | None:
    """Return the OpenRouter API key.

    Returns:
        str | None: OpenRouter API key or None.
    """
    value = os.getenv("OPENROUTER_API_KEY", "").strip()
    return value or None


def openrouter_model() -> str:
    """Return the OpenRouter model identifier (vendor/model).

    Returns:
        str: OpenRouter model name.
    """
    return os.getenv("OPENROUTER_MODEL", "openrouter/auto")


def openrouter_api_url() -> str:
    """Return the OpenRouter chat completions endpoint.

    Returns:
        str: OpenRouter API URL.
    """
    return os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")


def google_api_key() -> str | None:
    """Return the Google Gemini API key.

    Returns:
        str | None: Google API key or None.
    """
    return os.getenv("GOOGLE_API_KEY")


def google_model() -> str:
    """Return the Google Gemini model identifier.

    Returns:
        str: Gemini model identifier.
    """
    return os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")


def google_api_url() -> str:
    """Return the Google Gemini API base URL.

    Returns:
        str: Gemini API base URL.
    """
    return os.getenv("GOOGLE_API_URL", "https://generativelanguage.googleapis.com/v1beta")


def kodik_api_token() -> str | None:
    """Return the Kodik API token.

    Returns:
        str | None: Kodik token or None.
    """
    return _clean_secret(os.getenv("KODIK_API_TOKEN"))


def kodik_api_url() -> str:
    """Return the Kodik API base URL.

    Returns:
        str: Kodik API URL.
    """
    return os.getenv("KODIK_API_URL", "https://kodik-api.com")


def kodik_tokens_path() -> str:
    """Return the path to the Kodik public tokens file.

    Returns:
        str: Path to the tokens JSON file.
    """
    return os.getenv("KODIK_TOKENS_PATH", "kdk_tokns/tokens.json")


def anilibria_api_url() -> str:
    """Return the AniLibria API base URL.

    Returns:
        str: AniLibria API URL.
    """
    return os.getenv("ANILIBRIA_API_URL", "https://anilibria.top/api/v1")


def sameband_enabled() -> bool:
    """Return whether the SameBand SSR source is enabled.

    Returns:
        bool: True when SAMEBAND_ENABLED is enabled.
    """
    return os.getenv("SAMEBAND_ENABLED", "0") == "1"


def sameband_base_url() -> str:
    """Return the SameBand site base URL.

    Returns:
        str: SameBand base URL.
    """
    return os.getenv("SAMEBAND_BASE_URL", "https://sameband.studio")


def sameband_timeout() -> float:
    """Return the SameBand request timeout in seconds.

    Returns:
        float: SameBand timeout in seconds.
    """
    return float(os.getenv("SAMEBAND_TIMEOUT", "8"))


def aniboom_enabled() -> bool:
    """Return whether the AniBoom SSR source is enabled.

    Returns:
        bool: True when ANIBOOM_ENABLED is enabled.
    """
    return os.getenv("ANIBOOM_ENABLED", "0") == "1"


def aniboom_base_url() -> str:
    """Return the AniBoom player base URL.

    Returns:
        str: AniBoom base URL.
    """
    return os.getenv("ANIBOOM_BASE_URL", "https://aniboom.one")


def aniboom_timeout() -> float:
    """Return the AniBoom request timeout in seconds.

    Returns:
        float: AniBoom timeout in seconds.
    """
    return float(os.getenv("ANIBOOM_TIMEOUT", "8"))


def hanime_enabled() -> bool:
    """Return whether the Hanime.tv source is enabled.

    Returns:
        bool: True when HANIME_ENABLED is enabled.
    """
    return os.getenv("HANIME_ENABLED", "1") == "1"


def hanime_base_url() -> str:
    """Return the Hanime API base URL.

    Returns:
        str: Hanime base URL.
    """
    return os.getenv("HANIME_BASE_URL", "https://hanime.tv")


def hanime_timeout() -> float:
    """Return the Hanime request timeout in seconds.

    Returns:
        float: Hanime timeout in seconds.
    """
    return float(os.getenv("HANIME_TIMEOUT", "10"))


def hanime_proxy() -> str:
    """Return an optional proxy URL for the Hanime source.

    Returns:
        str: Proxy URL (http/socks5) or empty string for direct access.
    """
    return os.getenv("HANIME_PROXY", "")


def hanime_cf_clearance() -> str:
    """Return the Cloudflare cf_clearance cookie for Hanime.

    Returns:
        str: Cookie value or empty string when not configured.
    """
    return os.getenv("HANIME_CF_CLEARANCE", "")


def hanime_user_agent() -> str:
    """Return the User-Agent bound to the cf_clearance cookie.

    Returns:
        str: Browser User-Agent string.
    """
    return os.getenv(
        "HANIME_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    )


def media_proxy_upstream_proxy() -> str:
    """Return an optional proxy for upstream media streaming.

    Returns:
        str: Proxy URL (http) or empty string for direct access.
    """
    return os.getenv("MEDIA_PROXY_PROXY", "")


def kinobox_enabled() -> bool:
    """Return whether the Kinobox aggregator is enabled.

    Returns:
        bool: True when KINOBOX_ENABLED is enabled.
    """
    return os.getenv("KINOBOX_ENABLED", "1") == "1"


def kinobox_base_url() -> str:
    """Return the Kinobox API base URL.

    Returns:
        str: Kinobox base URL.
    """
    return os.getenv("KINOBOX_BASE_URL", "https://kinobox.tv")


def kinobox_timeout() -> float:
    """Return the Kinobox request timeout in seconds.

    Returns:
        float: Kinobox timeout in seconds.
    """
    return float(os.getenv("KINOBOX_TIMEOUT", "8"))


def animego_enabled() -> bool:
    """Return whether the AnimeGo scraper is enabled.

    Returns:
        bool: True when ANIMEGO_ENABLED is enabled.
    """
    return os.getenv("ANIMEGO_ENABLED", "1") == "1"


def animego_base_url() -> str:
    """Return the AnimeGo site base URL.

    Returns:
        str: AnimeGo base URL.
    """
    return os.getenv("ANIMEGO_BASE_URL", "https://animego.org")


def animego_timeout() -> float:
    """Return the AnimeGo request timeout in seconds.

    Returns:
        float: AnimeGo timeout in seconds.
    """
    return float(os.getenv("ANIMEGO_TIMEOUT", "10"))


def sibnet_enabled() -> bool:
    """Return whether the Sibnet extractor is enabled.

    Returns:
        bool: True when SIBNET_ENABLED is enabled.
    """
    return os.getenv("SIBNET_ENABLED", "1") == "1"


def eporner_enabled() -> bool:
    """Return whether the Eporner hentai/adult API source is enabled.

    Returns:
        bool: True when EPORNER_ENABLED is enabled.
    """
    return os.getenv("EPORNER_ENABLED", "1") == "1"


def eporner_base_url() -> str:
    """Return the Eporner API base URL.

    Returns:
        str: Eporner base URL.
    """
    return os.getenv("EPORNER_BASE_URL", "https://www.eporner.com")


def eporner_timeout() -> float:
    """Return the Eporner request timeout in seconds.

    Returns:
        float: Eporner timeout in seconds.
    """
    return float(os.getenv("EPORNER_TIMEOUT", "10"))


def sibnet_base_url() -> str:
    """Return the Sibnet video base URL.

    Returns:
        str: Sibnet base URL.
    """
    return os.getenv("SIBNET_BASE_URL", "https://video.sibnet.ru")


def sibnet_timeout() -> float:
    """Return the Sibnet request timeout in seconds.

    Returns:
        float: Sibnet timeout in seconds.
    """
    return float(os.getenv("SIBNET_TIMEOUT", "8"))


def rezka_enabled() -> bool:
    """Return whether the HDRezka parser is enabled.

    Returns:
        bool: True when REZKA_ENABLED is enabled.
    """
    return os.getenv("REZKA_ENABLED", "0") == "1"


def rezka_base_url() -> str:
    """Return the HDRezka site base URL (mirror).

    Returns:
        str: HDRezka base URL.
    """
    return os.getenv("REZKA_BASE_URL", "https://rezka.ag")


def rezka_timeout() -> float:
    """Return the HDRezka request timeout in seconds.

    Returns:
        float: HDRezka timeout in seconds.
    """
    return float(os.getenv("REZKA_TIMEOUT", "10"))


def youtube_api_key() -> str | None:
    """Return the YouTube Data API key.

    Returns:
        str | None: YouTube API key or None.
    """
    return _clean_secret(os.getenv("YOUTUBE_API_KEY"))


def youtube_api_url() -> str:
    """Return the YouTube Data API base URL.

    Returns:
        str: YouTube API URL.
    """
    return os.getenv("YOUTUBE_API_URL", "https://www.googleapis.com/youtube/v3")


def youtube_allowed_channel_ids() -> list[str]:
    """Return the allowed YouTube channel ids.

    Returns:
        list[str]: Allowed channel ids.
    """
    return [
        item.strip()
        for item in os.getenv("YOUTUBE_ALLOWED_CHANNEL_IDS", "").split(",")
        if item.strip()
    ]


def justwatch_partner_token() -> str | None:
    """Return the JustWatch partner token.

    Returns:
        str | None: JustWatch partner token or None.
    """
    return _clean_secret(os.getenv("JUSTWATCH_PARTNER_TOKEN"))


def justwatch_api_url() -> str:
    """Return the JustWatch content API URL.

    Returns:
        str: JustWatch API URL.
    """
    return os.getenv("JUSTWATCH_API_URL", "https://apis.justwatch.com/contentpartner/v2/content")


def justwatch_locale() -> str:
    """Return the JustWatch locale.

    Returns:
        str: JustWatch locale.
    """
    return os.getenv("JUSTWATCH_LOCALE", "en_US")


def telegram_support_bot_token() -> str | None:
    """Return the Telegram support bot token.

    Returns:
        str | None: Telegram bot token or None.
    """
    return os.getenv("TELEGRAM_SUPPORT_BOT_TOKEN")


def telegram_support_api_url() -> str:
    """Return the Telegram Bot API base URL.

    Returns:
        str: Telegram API URL.
    """
    return os.getenv("TELEGRAM_SUPPORT_API_URL", "https://api.telegram.org")


def telegram_support_admin_chat_ids() -> list[str]:
    """Return the Telegram admin chat ids for support alerts.

    Returns:
        list[str]: Admin chat ids.
    """
    return [
        item.strip()
        for item in os.getenv("TELEGRAM_SUPPORT_ADMIN_CHAT_IDS", "").split(",")
        if item.strip()
    ]


def support_email_to() -> list[str]:
    """Return the support recipient email addresses.

    Returns:
        list[str]: Recipient addresses.
    """
    return [item.strip() for item in os.getenv("SUPPORT_EMAIL_TO", "").split(",") if item.strip()]


def smtp_host() -> str | None:
    """Return the SMTP server host.

    Returns:
        str | None: SMTP host or None.
    """
    return os.getenv("SMTP_HOST")


def smtp_port() -> int:
    """Return the SMTP server port.

    Returns:
        int: SMTP port.
    """
    return int(os.getenv("SMTP_PORT", "587"))


def smtp_username() -> str | None:
    """Return the SMTP username.

    Returns:
        str | None: SMTP username or None.
    """
    return os.getenv("SMTP_USERNAME")


def smtp_password() -> str | None:
    """Return the SMTP password.

    Returns:
        str | None: SMTP password or None.
    """
    return os.getenv("SMTP_PASSWORD")


def smtp_from_email() -> str | None:
    """Return the SMTP sender address.

    Returns:
        str | None: SMTP sender or None.
    """
    return os.getenv("SMTP_FROM_EMAIL")


def smtp_use_tls() -> bool:
    """Return whether SMTP uses STARTTLS.

    Returns:
        bool: True when SMTP_USE_TLS is enabled.
    """
    return os.getenv("SMTP_USE_TLS", "1") == "1"
