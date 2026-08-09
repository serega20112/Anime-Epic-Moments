from __future__ import annotations

from html import escape

import requests

from backend.config import Settings
from backend.domain.support.entity import SupportTicket
from backend.infrastructure.external._async import external_method


class TelegramSupportNotifier:
    """Отправляет новые тикеты поддержки в Telegram."""

    def __init__(self):
        self.api_url = Settings.telegram_support_api_url.rstrip("/")
        self.bot_token = Settings.telegram_support_bot_token
        self.admin_chat_ids = Settings.telegram_support_admin_chat_ids
        self.session = requests.Session()
        self.session.trust_env = False

    def is_enabled(self) -> bool:
        """Возвращает доступность Telegram notifier по текущей конфигурации."""
        return bool(self.bot_token and self.admin_chat_ids)

    @external_method
    def send_ticket_created(self, ticket: SupportTicket) -> int:
        """Отправляет уведомление о новом тикете хотя бы в один admin chat."""
        if not self.bot_token or not self.admin_chat_ids:
            raise RuntimeError("Telegram support bot is not configured")

        delivered_count = 0
        errors: list[str] = []
        payload = {
            "text": self._build_message(ticket),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        for chat_id in self.admin_chat_ids:
            try:
                response = self.session.post(
                    f"{self.api_url}/bot{self.bot_token}/sendMessage",
                    json={**payload, "chat_id": chat_id},
                    timeout=25,
                )
                response.raise_for_status()
                body = response.json()
                if not body.get("ok"):
                    raise RuntimeError(str(body.get("description") or "telegram_api_error"))
                delivered_count += 1
            except (requests.RequestException, ValueError, TypeError, RuntimeError) as error:
                errors.append(str(error))

        if delivered_count > 0:
            return delivered_count

        detail = "; ".join(errors[:2]).strip()
        if detail:
            raise RuntimeError(f"Не удалось отправить тикет в Telegram: {detail}")
        raise RuntimeError("Не удалось отправить тикет в Telegram")

    def _build_message(self, ticket: SupportTicket) -> str:
        """Формирует HTML-сообщение Telegram для нового тикета."""
        created_at = ticket.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            "🛟 <b>Новый тикет поддержки</b>",
            f"<b>ID:</b> {ticket.id or 'new'}",
            f"<b>Пользователь:</b> {escape(ticket.username)}",
            f"<b>Email:</b> {escape(ticket.email)}",
            f"<b>User ID:</b> {ticket.user_id if ticket.user_id is not None else 'guest'}",
            f"<b>Тема:</b> {escape(self._truncate(ticket.subject, 160))}",
            f"<b>Создан:</b> {escape(created_at)}",
        ]
        if ticket.page_url:
            lines.append(f"<b>Страница:</b> {escape(self._truncate(ticket.page_url, 500))}")
        lines.extend(
            [
                "",
                "<b>Сообщение:</b>",
                escape(self._truncate(ticket.message, 2500)),
            ]
        )
        return "\n".join(lines)

    def _truncate(self, value: str | None, limit: int) -> str:
        """Обрезает длинный текст до безопасной длины для Telegram."""
        text = str(value or "").strip()
        if len(text) <= limit:
            return text
        return f"{text[: max(limit - 1, 1)].rstrip()}…"
