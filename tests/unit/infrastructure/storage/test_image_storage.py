from __future__ import annotations

from pathlib import Path

import pytest

from backend.application.interface.services.image_storage import ImageStorageError
from backend.infrastructure.storage import image_storage as storage_module
from backend.infrastructure.storage.image_storage import (
    FileSystemImageStorage,
    detect_image_format,
)

PNG_HEAD = b"\x89PNG\r\n\x1a\n"
JPEG_HEAD = b"\xff\xd8\xff\xe0"
GIF_HEAD = b"GIF89a"
WEBP_HEAD = b"RIFF\x00\x00\x00\x00WEBPVP8 "


class _Upload:
    """Минимальная замена Starlette UploadFile для тестов хранилища."""

    def __init__(self, filename: str, payload: bytes, content_type: str = "image/png") -> None:
        """Сохранить имя, содержимое и заявленный тип.

        Args:
            filename: Имя файла, присланное клиентом.
            payload: Байты содержимого.
            content_type: Заявленный клиентом Content-Type.
        """
        self.filename = filename
        self.content_type = content_type
        self._payload = payload
        self._position = 0

    async def read(self, size: int = -1) -> bytes:
        """Прочитать следующий фрагмент содержимого.

        Args:
            size: Размер фрагмента; -1 читает остаток.

        Returns:
            bytes: Очередные байты либо пустое значение в конце файла.
        """
        end = len(self._payload) if size < 0 else min(self._position + size, len(self._payload))
        chunk = self._payload[self._position : end]
        self._position = end
        return chunk


@pytest.fixture
def storage(tmp_path: Path) -> FileSystemImageStorage:
    """Собрать хранилище, указывающее на временный каталог теста.

    Args:
        tmp_path: Временный каталог pytest.

    Returns:
        FileSystemImageStorage: Хранилище, пишущее вне дерева репозитория.
    """
    return FileSystemImageStorage(uploads_root=tmp_path / "uploads")


@pytest.mark.unit
class TestDetectImageFormat:
    """Юнит-тесты распознавания формата изображения по содержимому."""

    @pytest.mark.parametrize(
        ("head", "expected"),
        [
            (PNG_HEAD + b"\x00" * 8, "png"),
            (JPEG_HEAD + b"\x00" * 8, "jpg"),
            (GIF_HEAD + b"\x00" * 8, "gif"),
            (WEBP_HEAD, "webp"),
        ],
    )
    def test_recognizes_supported_formats(self, head: bytes, expected: str):
        """Что тестируем: detect_image_format на поддерживаемых сигнатурах.
        Что передаём: заголовки png, jpg, gif и webp.
        Что ожидаем: формат распознан по содержимому, а не по имени файла.
        """
        assert detect_image_format(head) == expected

    @pytest.mark.parametrize("head", [b"BM\x00\x00\x00\x00", b"<html>" * 3, b"", b"\x00" * 12])
    def test_rejects_non_images(self, head: bytes):
        """Что тестируем: detect_image_format на постороннем содержимом.
        Что передаём: bmp-заголовок, HTML и пустоту.
        Что ожидаем: None — такие файлы в хранилище не попадают.
        """
        assert detect_image_format(head) is None

    def test_rejects_riff_without_webp_marker(self):
        """Что тестируем: RIFF-контейнер без метки WEBP.
        Что передаём: заголовок RIFF с произвольным содержимым.
        Что ожидаем: None, иначе wav- или avi-файл сошёл бы за изображение.
        """
        assert detect_image_format(b"RIFF\x00\x00\x00\x00WAVE") is None


@pytest.mark.unit
class TestFileSystemImageStorage:
    """Юнит-тесты файлового хранилища загружаемых изображений."""

    async def test_stores_file_with_detected_extension(
        self, storage: FileSystemImageStorage, tmp_path: Path
    ):
        """Что тестируем: save для валидного png под ложным именем.
        Что передаём: содержимое png и имя ``photo.txt``.
        Что ожидаем: файл сохранён со случайным именем и расширением png.
        """
        upload = _Upload("photo.txt", PNG_HEAD + b"\x00" * 40)

        url = await storage.save(upload, "avatars")

        assert url.startswith("/static/uploads/avatars/")
        assert url.endswith(".png")
        saved = list((tmp_path / "uploads" / "avatars").iterdir())
        assert len(saved) == 1
        assert saved[0].name != "photo.txt"

    async def test_rejects_non_image_payload(self, storage: FileSystemImageStorage, tmp_path: Path):
        """Что тестируем: загрузку HTML под расширением png (регрессия S3.4).
        Что передаём: текстовое содержимое с image-именем и image Content-Type.
        Что ожидаем: ImageStorageError, файл на диск не записан.
        """
        upload = _Upload("x.png", b"<html><script>alert(1)</script></html>")

        with pytest.raises(ImageStorageError):
            await storage.save(upload, "avatars")

        assert not (tmp_path / "uploads" / "avatars").exists()

    async def test_rejects_path_traversal_subdir(self, storage: FileSystemImageStorage):
        """Что тестируем: каталог загрузки с путь-трaversal.
        Что передаём: subdir ``../evil``.
        Что ожидаем: ImageStorageError, запись вне корня невозможна.
        """
        upload = _Upload("p.png", PNG_HEAD + b"\x00" * 40)

        with pytest.raises(ImageStorageError):
            await storage.save(upload, "../evil")

    async def test_rejects_oversized_file(
        self, storage: FileSystemImageStorage, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Что тестируем: превышение лимита размера.
        Что передаём: изображение с лимитом в 8 байт и содержимым длиннее.
        Что ожидаем: ImageStorageError, частичный файл удалён.
        """
        monkeypatch.setattr(storage_module, "MAX_IMAGE_BYTES", 8)
        upload = _Upload("p.png", PNG_HEAD + b"\x00" * 64)

        with pytest.raises(ImageStorageError):
            await storage.save(upload, "covers")

        assert not list((tmp_path / "uploads" / "covers").iterdir())

    async def test_rejects_empty_and_missing_upload(self, storage: FileSystemImageStorage):
        """Что тестируем: пустой файл и отсутствие файла.
        Что передаём: пустое содержимое и None.
        Что ожидаем: ImageStorageError в обоих случаях.
        """
        with pytest.raises(ImageStorageError):
            await storage.save(_Upload("p.png", b""), "avatars")
        with pytest.raises(ImageStorageError):
            await storage.save(None, "avatars")
