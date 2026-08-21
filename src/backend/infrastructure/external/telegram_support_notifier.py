from __future__ import annotations

from html import escape

import httpx

from backend.config import Settings
from backend.domain.entities.support.support_ticket import SupportTicket
from backend.infrastructure.external.errors import (
    ExternalServiceConfigurationError,
    ExternalServiceInvalidResponseError,
    ExternalServiceUnavailableError,
)


class TelegramSupportNotifier:
    """Отправляет новые тикеты поддержки в Telegram."""

    def __init__(self):
        self.api_url = Settings.telegram_support_api_url.rstrip("/")
        self.bot_token = Settings.telegram_support_bot_token
        self.admin_chat_ids = Settings.telegram_support_admin_chat_ids
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(6),
            trust_env=False,
            follow_redirects=True,
        )

    async def is_enabled(self) -> bool:
        """Возвращает доступность Telegram notifier по текущей конфигурации."""
        return bool(self.bot_token and self.admin_chat_ids)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self.session.aclose()

    async def send_ticket_created(self, ticket: SupportTicket) -> int:
        """Отправляет уведомление о новом тикете хотя бы в один admin chat."""
        if not self.bot_token or not self.admin_chat_ids:
            raise ExternalServiceConfigurationError(
                "Telegram support bot is not configured", service_name="telegram"
            )

        delivered_count = 0
        errors: list[str] = []
        payload = {
            "text": await self._build_message(ticket),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        for chat_id in self.admin_chat_ids:
            try:
                response = await self.session.post(
                    f"{self.api_url}/bot{self.bot_token}/sendMessage",
                    json={**payload, "chat_id": chat_id},
                )
                response.raise_for_status()
                body = response.json()
                if not body.get("ok"):
                    raise ExternalServiceInvalidResponseError(
                        str(body.get("description") or "telegram_api_error"),
                        service_name="telegram",
                    )
                delivered_count += 1
            except (
                httpx.HTTPError,
                ValueError,
                TypeError,
                ExternalServiceInvalidResponseError,
            ) as error:
                errors.append(str(error))

        if delivered_count > 0:
            return delivered_count

        detail = "; ".join(errors[:2]).strip()
        if detail:
            raise ExternalServiceUnavailableError(
                f"Не удалось отправить тикет в Telegram: {detail}",
                service_name="telegram",
            )
        raise ExternalServiceUnavailableError(
            "Не удалось отправить тикет в Telegram", service_name="telegram"
        )

    async def _build_message(self, ticket: SupportTicket) -> str:
        """Формирует HTML-сообщение Telegram для нового тикета."""
        created_at = ticket.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            "🛟 <b>Новый тикет поддержки</b>",
            f"<b>ID:</b> {ticket.id or 'new'}",
            f"<b>Пользователь:</b> {escape(ticket.username)}",
            f"<b>Email:</b> {escape(ticket.email)}",
            f"<b>User ID:</b> {ticket.user_id if ticket.user_id is not None else 'guest'}",
            f"<b>Тема:</b> {escape(await self._truncate(ticket.subject, 160))}",
            f"<b>Создан:</b> {escape(created_at)}",
        ]
        if ticket.page_url:
            lines.append(f"<b>Страница:</b> {escape(await self._truncate(ticket.page_url, 500))}")
        lines.extend(
            [
                "",
                "<b>Сообщение:</b>",
                escape(await self._truncate(ticket.message, 2500)),
            ]
        )
        return "\n".join(lines)

    async def _truncate(self, value: str | None, limit: int) -> str:
        """Обрезает длинный текст до безопасной длины для Telegram."""
        text = str(value or "").strip()
        if len(text) <= limit:
            return text
        return f"{text[: max(limit - 1, 1)].rstrip()}…"
