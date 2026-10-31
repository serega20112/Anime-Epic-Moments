# Онбординг разработчика

## Описание

Документ описывает путь от чистого компьютера до запущенного **AEM** с
зелёными гейтами качества. Все команды кроссплатформенные: они не зависят от
оболочки и не требуют переменных окружения вроде `PYTHONPATH`.

## Что нужно перед началом

| Инструмент | Версия | Зачем |
| --- | --- | --- |
| Python | 3.12 (строго `>=3.12,<3.13`) | Версия зафиксирована в `requires-python` и `.python-version` |
| [uv](https://docs.astral.sh/uv/) | `>=0.10` | Менеджер зависимостей и запускатор команд; `required-version` проверяется при каждом вызове |
| Docker с плагином Compose | любая актуальная | PostgreSQL и Redis локально; без Docker нужны собственные инстансы |
| Git | любая актуальная | Ветки, хуки, история |

Нативный интерпретатор 3.12 устанавливать не обязательно: в `pyproject.toml`
стоит `python-preference = "only-managed"`, поэтому `uv` сам скачает и заведёт
нужный CPython в своём каталоге.

## Пошаговый сетап

### 1. Клонирование и зависимости

```bash
git clone https://github.com/serega20112/Anime-Epic-Moments.git
cd Anime-Epic-Moments
uv sync
```

`uv sync` ставит основную группу и обе группы `dev` и `lint` — они объявлены
группами по умолчанию (`default-groups`), поэтому отдельный флаг не нужен.
Полный набор для тестов и проверок приходит сразу.

### 2. Переменные окружения

```bash
cp .env.example .env
```

После копирования обязательно правятся:

| Переменная | Почему сразу |
| --- | --- |
| `SECRET_KEY` | Вне отладки приложение не стартует без ключа подписи |
| `DATABASE_URL` или `POSTGRES_*` | Указывают на локальную базу из compose |
| `REDIS_URL` | По умолчанию `redis://localhost:6379/0` — совпадает с compose |
| `KODIK_API_TOKEN` | Без него провайдер Kodik остаётся выключенным |

Значения-заглушки (`your-...`, `change-me-...`, `xxx...`) приложение считает
отсутствующими: скопированный пример не приведёт к запросам с неверным
токеном, но и не заработает, пока значение не заменено. Полная таблица
переменных — в [справочнике](../03-ops/env-reference.md).

### 3. Инфраструктура

```bash
docker compose up -d postgres redis
```

Поднимаются только база и кэш: приложение запускается нативно, чтобы работал
`--reload`. Redis GUI (`redis_commander`) для разработки не нужен, но доступен
той же командой без списка сервисов.

### 4. Схема базы

```bash
uv run alembic -c migrations/alembic.ini upgrade head
```

Единственный источник схемы — Alembic. Создавать таблицы через
`DATABASE_AUTO_INIT=1` не нужно: ревизия `a0c0657fa309` поднимает схему с нуля.

### 5. Запуск приложения

```bash
uv run uvicorn backend.main:app --app-dir src --reload --port 5000
```

`--app-dir src` добавляет каталог с исходниками в путь импорта. Это заменяет
переменную `PYTHONPATH` из примеров прошлых лет и работает одинаково в любой
оболочке. Открыть: <http://localhost:5000>, документация —
<http://localhost:5000/docs>.

### 6. Pre-commit

```bash
uv run pre-commit install
```

Хуки запускаются на каждый коммит:

| Хук | Что делает |
| --- | --- |
| `ruff-check` | `uv run ruff check src tests --fix` |
| `ruff-format` | `uv run ruff format src tests` |
| `lint-imports` | Проверка границ слоёв: import-linter с добавлением `src` в путь импорта |
| `pytest-unit` | `uv run pytest tests/unit -q --no-cov` |

Прогнать всё по репозиторию без коммита: `uv run pre-commit run --all-files`.

### 7. IDE

Для PyCharm и VS Code достаточно двух настроек:

- интерпретатор — `.venv` в корне репозитория;
- каталог `src` помечен как источник (`Sources Root`), чтобы `backend.*`
  разрешался без правки `PYTHONPATH`.

`pytest` настроен в `pyproject.toml` (`pythonpath = ["src"]`), поэтому тесты из
IDE запускаются без дополнительной конфигурации.

## Ежедневный цикл

| Задача | Команда |
| --- | --- |
| Подтянуть зависимости | `uv sync` |
| Поднять инфраструктуру | `docker compose up -d postgres redis` |
| Применить миграции | `uv run alembic -c migrations/alembic.ini upgrade head` |
| Запустить приложение | `uv run uvicorn backend.main:app --app-dir src --reload --port 5000` |
| Линтер | `uv run ruff check src tests migrations` |
| Формат | `uv run ruff format src tests migrations` |
| Границы слоёв | `uv run python scripts/check_imports.py` |
| Докстринги и комментарии | `uv run python scripts/check_style.py` |
| Контракт OpenAPI | `uv run python scripts/export_openapi.py --check` |
| Тесты | `uv run pytest` |
| Быстрые тесты без покрытия | `uv run pytest -q --no-cov` |
| Только unit | `uv run pytest tests/unit -q --no-cov` |
| Соответствие `uv.lock` | `uv lock --check` |

`uv run pytest` по умолчанию включает покрытие и падает при просадке ниже порога
`fail_under`. Для быстрой итерации берите `--no-cov`.

Те же проверки выполняет CI в `.github/workflows/ci.yml`, плюс отдельная job
поднимает PostgreSQL, прогоняет `upgrade head`, `alembic check`, полный цикл
`downgrade base` → `upgrade head` и интеграционные тесты репозиториев.

### Контейнерный запуск для проверки образа

Иногда нужно повторить поведение продакшена, не выходя из репозитория:

```bash
docker compose up -d --build
docker compose logs -f app
```

Режим разработки внутри контейнера с автоперезагрузкой:

```bash
docker compose run --rm --service-ports app dev
```

Подробности — в [развёртывании](../03-ops/deployment.md).

## Частые проблемы

| Симптом | Причина | Решение |
| --- | --- | --- |
| `uv: command not found` | uv не установлен или не в `PATH` | Установить по инструкции uv и перезапустить терминал |
| `Could not find package 'backend' in your Python path` | `lint-imports` запущен напрямую без `src` в пути | Использовать `uv run python scripts/check_imports.py` |
| `ModuleNotFoundError: backend` при запуске | Пропущен `--app-dir src` | Добавить флаг либо пометить `src` как источник в IDE |
| Приложение падает на старте из-за `SECRET_KEY` | `APP_DEBUG=0` и пустой ключ | Заполнить `SECRET_KEY` в `.env` |
| `password authentication failed for user` | Том `postgres_data` создан с другими `POSTGRES_*` | Пользователь создаётся только при инициализации тома: сменить креды в `.env` под существующие или пересоздать том |
| `alembic upgrade head` не подключается | База ещё поднимается | Повторить через несколько секунд или дождаться healthcheck |
| Провайдер не отдаёт источники | Токен оставлен заглушкой или `*_ENABLED=0` | Проверить значение в `.env` и записи в логе |
| `alembic check` показывает дифф | Модель изменена без ревизии | Создать ревизию: `uv run alembic -c migrations/alembic.ini revision --autogenerate -m "..."` |
| Хук `pytest-unit` падает на «неизвестном» тесте | Тест требует базы или сети | Такие тесты живут в `tests/integration` и в хук не входят |

## Почему это сделано так

Единственный менеджер зависимостей — `uv`: один файл `uv.lock` фиксирует весь
граф, `uv sync` воспроизводит окружение, `uv run` избавляет от активации
виртуального окружения. Пока `requirements.txt` и `poetry` в проекте нет,
источник зависимостей ровно один, и расхождение «локально работает, в CI нет»
сводится к проверке `uv lock --check`.

Флаг `--app-dir src` выбран вместо переменных оболочки, потому что проект
разрабатывается на разных ОС: команда с `PYTHONPATH=src` или
`$env:PYTHONPATH="src"` работает только в одной из них, а флаг — везде.

Инфраструктура в Docker, приложение нативно: перезагрузка кода занимает
секунды, а PostgreSQL и Redis ведут себя так же, как в бою. Полный контейнерный
запуск остаётся для проверки образа и для повторения продакшн-поведения.

Скрипты `scripts/*.py` для гейтов появились из-за той же кроссплатформенности:
`lint-imports` и генераторы артефактов должны сами добавлять `src` в путь
импорта, иначе каждая ОС требовала бы своей обёртки. Проверка `uv run` +
`python scripts/...` читается одинаково в любом терминале и в CI.

## Где в коде

- [`pyproject.toml`](../../pyproject.toml) — зависимости, группы, `pytest`, `import-linter`, покрытие
- [`ruff.toml`](../../ruff.toml) — правила линтера и форматтера
- [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) — хуки
- [`scripts/check_imports.py`](../../scripts/check_imports.py), [`scripts/check_style.py`](../../scripts/check_style.py) — гейты
- [`src/backend/main.py`](../../src/backend/main.py) — точка входа приложения
- [`.env.example`](../../.env.example) — шаблон окружения

## Связанные документы

- [Соглашения кодовой базы](conventions.md)
- [Как добавить фичу](feature-workflow.md)
- [Переменные окружения](../03-ops/env-reference.md)
- [Развёртывание](../03-ops/deployment.md)
- [Слои и правила](../01-architecture/layers-and-rules.md)
