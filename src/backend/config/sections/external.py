"""External service integration settings."""

from __future__ import annotations

import os


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
    return os.getenv(
        "HF_API_URL", "https://router.huggingface.co/v1/chat/completions"
    )


def kodik_api_token() -> str | None:
    """Return the Kodik API token.

    Returns:
        str | None: Kodik token or None.
    """
    return os.getenv("KODIK_API_TOKEN")


def kodik_api_url() -> str:
    """Return the Kodik API base URL.

    Returns:
        str: Kodik API URL.
    """
    return os.getenv("KODIK_API_URL", "https://kodik-api.com")


def anilibria_api_url() -> str:
    """Return the AniLibria API base URL.

    Returns:
        str: AniLibria API URL.
    """
    return os.getenv("ANILIBRIA_API_URL", "https://anilibria.top/api/v1")


def youtube_api_key() -> str | None:
    """Return the YouTube Data API key.

    Returns:
        str | None: YouTube API key or None.
    """
    return os.getenv("YOUTUBE_API_KEY")


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
    return os.getenv("JUSTWATCH_PARTNER_TOKEN")


def justwatch_api_url() -> str:
    """Return the JustWatch content API URL.

    Returns:
        str: JustWatch API URL.
    """
    return os.getenv(
        "JUSTWATCH_API_URL", "https://apis.justwatch.com/contentpartner/v2/content"
    )


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
    return [
        item.strip() for item in os.getenv("SUPPORT_EMAIL_TO", "").split(",") if item.strip()
    ]


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