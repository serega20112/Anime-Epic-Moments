"""Web utilities facade: template rendering and flash messaging."""

from backend.infrastructure.web.templating import (
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
