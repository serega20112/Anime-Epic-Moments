"""Файловое хранилище загружаемых изображений.

Файлы кладутся под каталог статики фронтенда, чтобы они отдавались монтированием
``/static`` без дополнительной маршрутизации. Имя всегда генерируется случайное
(UUID), а расширение берётся из определённого по содержимому формата: имена и
``Content-Type`` клиента файловой системе не диктуются.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from backend.application.interface.services.image_storage import (
    ImageStorageError,
    ImageStoragePort,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
STATIC_ROOT = PROJECT_ROOT / "src" / "frontend" / "static"
UPLOADS_ROOT = STATIC_ROOT / "uploads"

MAX_IMAGE_BYTES = 5 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
SNIFF_BYTES = 12
SUBDIR_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")

MISSING_FILE_MESSAGE = "Файл не выбран"
SUBDIR_MESSAGE = "Недопустимый каталог загрузки"
TOO_LARGE_MESSAGE = "Файл больше 5 МБ"
EMPTY_MESSAGE = "Файл пустой"
NOT_IMAGE_MESSAGE = "Содержимое файла не является изображением"

IMAGE_SIGNATURES: tuple[tuple[bytes, int, str], ...] = (
    (b"\xff\xd8\xff", 0, "jpg"),
    (b"\x89PNG\r\n\x1a\n", 0, "png"),
    (b"GIF87a", 0, "gif"),
    (b"GIF89a", 0, "gif"),
    (b"RIFF", 0, "webp"),
)
WEBP_MARKER = b"WEBP"
WEBP_MARKER_OFFSET = 8


def detect_image_format(head: bytes) -> str | None:
    """Определить формат изображения по сигнатуре содержимого.

    Проверка по ``Content-Type`` и расширению клиента ненадёжна: оба значения
    контролирует атакующий, поэтому каноническим источником типа считается
    заголовок самого файла.

    Args:
        head: Первые байты загруженного файла.

    Returns:
        str | None: Расширение формата (``jpg``, ``png``, ``gif``, ``webp``)
            либо None, если содержимое не похоже на изображение.
    """
    for prefix, offset, extension in IMAGE_SIGNATURES:
        if not head.startswith(prefix, offset):
            continue
        if extension == "webp":
            marker = head[WEBP_MARKER_OFFSET : WEBP_MARKER_OFFSET + len(WEBP_MARKER)]
            if marker != WEBP_MARKER:
                continue
        return extension
    return None


class FileSystemImageStorage(ImageStoragePort):
    """Хранилище картинок на локальном диске под каталогом статики."""

    def __init__(self, uploads_root: Path = UPLOADS_ROOT) -> None:
        """Указать корень загрузок.

        Args:
            uploads_root: Каталог внутри статики, куда кладутся файлы.
        """
        self.uploads_root = uploads_root

    async def save(self, upload, subdir: str) -> str:
        """Сохранить загруженное изображение и вернуть его публичный URL.

        Args:
            upload: ``UploadFile`` из multipart-формы.
            subdir: Подкаталог внутри корня загрузок, безопасное slug-имя.

        Returns:
            str: Публичный URL вида ``/static/uploads/<subdir>/<name>``.

        Raises:
            ImageStorageError: Файл отсутствует, каталог недопустим, формат не
                распознан по содержимому либо размер превышает лимит.
        """
        if upload is None or not getattr(upload, "filename", None):
            raise ImageStorageError(MISSING_FILE_MESSAGE)
        if not SUBDIR_PATTERN.match(str(subdir or "")):
            raise ImageStorageError(SUBDIR_MESSAGE)

        first_chunk = await upload.read(CHUNK_BYTES)
        if not first_chunk:
            raise ImageStorageError(EMPTY_MESSAGE)
        extension = detect_image_format(first_chunk[:SNIFF_BYTES])
        if extension is None:
            raise ImageStorageError(NOT_IMAGE_MESSAGE)

        target_dir = self.uploads_root / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{uuid.uuid4().hex}.{extension}"
        written = await self._write_stream(upload, target_path, first_chunk)
        if written == 0:
            target_path.unlink(missing_ok=True)
            raise ImageStorageError(EMPTY_MESSAGE)
        return f"/static/uploads/{subdir}/{target_path.name}"

    async def _write_stream(self, upload, target_path: Path, first_chunk: bytes) -> int:
        """Записать поток файла на диск, следя за лимитом размера.

        Args:
            upload: Источник байтов.
            target_path: Куда писать.
            first_chunk: Уже прочитанный первый блок.

        Returns:
            int: Число записанных байтов.

        Raises:
            ImageStorageError: Файл больше разрешённого; частичная запись удаляется.
        """
        written = 0
        chunk = first_chunk
        with target_path.open("wb") as destination:
            while chunk:
                written += len(chunk)
                if written > MAX_IMAGE_BYTES:
                    destination.close()
                    target_path.unlink(missing_ok=True)
                    raise ImageStorageError(TOO_LARGE_MESSAGE)
                destination.write(chunk)
                chunk = await upload.read(CHUNK_BYTES)
        return written
