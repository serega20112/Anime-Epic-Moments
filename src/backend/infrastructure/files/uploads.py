"""Filesystem storage for user-uploaded images.

Uploaded files are stored under the frontend static directory so they are
served directly by the ``/static`` mount without extra routing. Every file
gets a random UUID name: user-supplied names never touch the filesystem.
"""

from __future__ import annotations

import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATIC_ROOT = PROJECT_ROOT / "src" / "frontend" / "static"
UPLOADS_ROOT = STATIC_ROOT / "uploads"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class UploadValidationError(ValueError):
    """Raised when an uploaded file is not a valid stored image."""


async def save_image(upload, subdir: str) -> str:
    """Persist an uploaded image and return its public static URL.

    Args:
        upload: Starlette ``UploadFile`` from a multipart form.
        subdir: Storage subdirectory under ``static/uploads``.

    Returns:
        str: Public URL like ``/static/uploads/<subdir>/<name>``.

    Raises:
        UploadValidationError: When the file is missing, has a disallowed
            extension or content type, or exceeds the size limit.
    """
    if upload is None or not getattr(upload, "filename", None):
        raise UploadValidationError("Файл не выбран")
    extension = Path(str(upload.filename)).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise UploadValidationError("Допустимы только jpg, png, webp и gif")
    content_type = str(getattr(upload, "content_type", "") or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise UploadValidationError("Файл должен быть изображением")

    target_dir = UPLOADS_ROOT / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{uuid.uuid4().hex}{extension}"

    written = 0
    with target_path.open("wb") as destination:
        while chunk := await upload.read(64 * 1024):
            written += len(chunk)
            if written > MAX_IMAGE_BYTES:
                destination.close()
                target_path.unlink(missing_ok=True)
                raise UploadValidationError("Файл больше 5 МБ")
            destination.write(chunk)
    if written == 0:
        target_path.unlink(missing_ok=True)
        raise UploadValidationError("Файл пустой")
    return f"/static/uploads/{subdir}/{target_path.name}"
