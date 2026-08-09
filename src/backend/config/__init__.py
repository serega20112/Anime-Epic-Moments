"""Application configuration package.

Re-exports the settings singleton so consumers can use
``from backend.config import Settings``.
"""

from backend.config.settings import Settings

__all__ = ["Settings"]