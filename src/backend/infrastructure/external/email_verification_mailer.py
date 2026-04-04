import smtplib
from email.message import EmailMessage
from html import escape

from src.backend.dependencies.settings import Settings


class EmailVerificationMailer:
    """Отправляет письмо с кодом подтверждения email."""

    def send_verification_code(
        self,
        email: str,
        code: str,
        theme: str = "neon",
    ) -> None:
        """Отправляет одноразовый код подтверждения на email пользователя."""
        if not Settings.smtp_host or not Settings.smtp_from_email:
            raise RuntimeError("SMTP settings are not configured")

        normalized_theme = self._normalize_theme(theme)
        message = EmailMessage()
        message["Subject"] = "Anime Epic Moments: подтверждение email"
        message["From"] = Settings.smtp_from_email
        message["To"] = email
        message.set_content(
            "Подтверди email для Anime Epic Moments.\n\n"
            f"Код подтверждения: {code}\n\n"
            f"Код действует {Settings.email_verification_expire_minutes} минут.\n"
            f"Тема письма: {self._theme_label(normalized_theme)}."
        )
        message.add_alternative(
            self._build_html_message(code=code, theme=normalized_theme),
            subtype="html",
        )

        try:
            with smtplib.SMTP(Settings.smtp_host, Settings.smtp_port, timeout=30) as smtp:
                if Settings.smtp_use_tls:
                    smtp.starttls()
                if Settings.smtp_username and Settings.smtp_password:
                    smtp.login(Settings.smtp_username, Settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise RuntimeError(
                "Не удалось отправить письмо с кодом подтверждения. Проверь SMTP-настройки и сетевой доступ."
            ) from error

    def _build_html_message(self, code: str, theme: str) -> str:
        palette = self._palette(theme)
        title = escape(self._theme_title(theme))
        label = escape(self._theme_label(theme))
        safe_code = escape(code)
        safe_minutes = escape(str(Settings.email_verification_expire_minutes))
        return (
            "<!doctype html>"
            "<html lang='ru'>"
            "<body style=\"margin:0;padding:0;background:"
            f"{palette['page_background']};font-family:Inter,Segoe UI,Arial,sans-serif;color:{palette['text']};\">"
            "<div style='padding:32px 16px;'>"
            "<div style='max-width:560px;margin:0 auto;"
            f"background:{palette['card_background']};border:1px solid {palette['border']};"
            "border-radius:24px;overflow:hidden;"
            f"box-shadow:{palette['shadow']};'>"
            "<div style='padding:28px 28px 16px;"
            f"background:{palette['hero_background']};'>"
            "<div style='display:inline-block;padding:6px 12px;border-radius:999px;"
            f"background:{palette['badge_background']};color:{palette['badge_text']};"
            "font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;'>"
            f"{label}</div>"
            f"<h1 style='margin:18px 0 8px;font-size:28px;line-height:1.2;color:{palette['title']};'>{title}</h1>"
            f"<p style='margin:0;font-size:15px;line-height:1.6;color:{palette['muted']};'>"
            "Подтверди почту для Anime Epic Moments и заверши регистрацию."
            "</p>"
            "</div>"
            "<div style='padding:28px;'>"
            f"<div style='font-size:13px;line-height:1.5;color:{palette['muted']};margin-bottom:10px;'>"
            "Код подтверждения"
            "</div>"
            "<div style='padding:18px 20px;border-radius:18px;text-align:center;"
            f"background:{palette['code_background']};border:1px solid {palette['code_border']};"
            f"color:{palette['code_text']};font-size:34px;font-weight:800;letter-spacing:0.28em;'>"
            f"{safe_code}</div>"
            f"<p style='margin:18px 0 0;font-size:14px;line-height:1.7;color:{palette['muted']};'>"
            f"Код действует {safe_minutes} минут. Если это не ты, просто проигнорируй письмо."
            "</p>"
            "</div>"
            "</div>"
            "</div>"
            "</body>"
            "</html>"
        )

    def _normalize_theme(self, value: str | None) -> str:
        normalized = str(value or "").strip().lower()
        return normalized if normalized in {"neon", "dark", "light", "rose"} else "neon"

    def _theme_label(self, theme: str) -> str:
        labels = {
            "neon": "Неоновая тема",
            "dark": "Тёмная тема",
            "light": "Светлая тема",
            "rose": "Тема сакуры",
        }
        return labels[theme]

    def _theme_title(self, theme: str) -> str:
        titles = {
            "neon": "Подтверждение почты в неоновом стиле",
            "dark": "Подтверждение почты в тёмной теме",
            "light": "Подтверждение почты в светлой теме",
            "rose": "Подтверждение почты в теме сакуры",
        }
        return titles[theme]

    def _palette(self, theme: str) -> dict[str, str]:
        palettes = {
            "neon": {
                "page_background": "#050816",
                "card_background": "#0e1634",
                "hero_background": "linear-gradient(135deg, #101a42 0%, #1d0f34 100%)",
                "border": "#29407c",
                "shadow": "0 28px 80px rgba(0, 0, 0, 0.45)",
                "badge_background": "#ff4fd8",
                "badge_text": "#ffffff",
                "title": "#f6f7ff",
                "text": "#e8ebff",
                "muted": "#b6c0ef",
                "code_background": "#111b44",
                "code_border": "#34d8ff",
                "code_text": "#9ef3ff",
            },
            "dark": {
                "page_background": "#050505",
                "card_background": "#111111",
                "hero_background": "linear-gradient(135deg, #101010 0%, #1b1b1b 100%)",
                "border": "#2b2b2b",
                "shadow": "0 28px 80px rgba(0, 0, 0, 0.6)",
                "badge_background": "#f0f0f0",
                "badge_text": "#121212",
                "title": "#ffffff",
                "text": "#f5f5f5",
                "muted": "#b5b5b5",
                "code_background": "#161616",
                "code_border": "#3a3a3a",
                "code_text": "#ffffff",
            },
            "light": {
                "page_background": "#f5f0e8",
                "card_background": "#fffaf3",
                "hero_background": "linear-gradient(135deg, #fff7eb 0%, #f1e6d8 100%)",
                "border": "#dcc9b3",
                "shadow": "0 24px 60px rgba(89, 63, 34, 0.18)",
                "badge_background": "#d3a15d",
                "badge_text": "#ffffff",
                "title": "#4a3522",
                "text": "#3e2d1f",
                "muted": "#725943",
                "code_background": "#fff2df",
                "code_border": "#ddb375",
                "code_text": "#5b3d21",
            },
            "rose": {
                "page_background": "#130810",
                "card_background": "#22101b",
                "hero_background": "linear-gradient(135deg, #341425 0%, #51203a 100%)",
                "border": "#70314d",
                "shadow": "0 28px 70px rgba(0, 0, 0, 0.38)",
                "badge_background": "#ff7eab",
                "badge_text": "#ffffff",
                "title": "#fff1f6",
                "text": "#ffe3ed",
                "muted": "#d3a6b8",
                "code_background": "#2c1121",
                "code_border": "#ff9cc0",
                "code_text": "#ffd1e0",
            },
        }
        return palettes[theme]
