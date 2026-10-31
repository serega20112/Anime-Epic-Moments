"""Фасад подпакета хранилищ файлов."""

from __future__ import annotations

from backend.infrastructure.storage.image_storage import FileSystemImageStorage

__all__ = ["FileSystemImageStorage"]
