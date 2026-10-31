"""Точка входа приложения: собирает FastAPI-приложение и запускает локальный dev-сервер.

Модуль импортируется как `backend.main` (в контейнере — gunicorn с `backend.main:app`),
поэтому все импорты внутри проекта используют один и тот же корневой пакет `backend`.
"""

from __future__ import annotations

import uvicorn

from backend.config import Settings
from backend.presentation.app_factory import create_app

app = create_app()


def main() -> None:
    """Запустить uvicorn для локальной разработки.

    Приложение передаётся import-строкой, а не объектом: uvicorn умеет перезагружать
    процесс только при наличии строки, иначе запуск с `APP_DEBUG=1` завершается ошибкой.
    """
    uvicorn.run(
        "backend.main:app",
        host=Settings.app_host,
        port=Settings.app_port,
        reload=Settings.app_debug,
    )


if __name__ == "__main__":
    main()
