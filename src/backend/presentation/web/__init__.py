"""Фасад web-инструментов presentation-слоя: шаблоны и flash-сообщения."""

from __future__ import annotations

from backend.presentation.web.templating import (
    TemplateRequestProxy,
    flash,
    pop_flashed_messages,
    render_template,
)

__all__ = [
    "TemplateRequestProxy",
    "flash",
    "pop_flashed_messages",
    "render_template",
]
