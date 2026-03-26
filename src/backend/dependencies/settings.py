import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Настройки приложения
    """
    secret_key: str = os.getenv("SECRET_KEY", "epic-anime-secret-key-123")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///anime_epic_moments.db")
    hf_token: str | None = os.getenv("HF_TOKEN")
    hf_provider: str | None = os.getenv("HF_PROVIDER", "fireworks-ai")
    hf_model: str = os.getenv("HF_MODEL", "openai/gpt-oss-120b")
    hf_api_url: str = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")
    kodik_api_token: str | None = os.getenv("KODIK_API_TOKEN")
    kodik_api_url: str = os.getenv("KODIK_API_URL", "https://kodik-api.com")
    flask_host: str = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port: int = int(os.getenv("FLASK_PORT", "5000"))
    flask_debug: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    app_base_url: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")
    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    smtp_from_email: str | None = os.getenv("SMTP_FROM_EMAIL")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "1") == "1"
    password_reset_expire_minutes: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30"))
