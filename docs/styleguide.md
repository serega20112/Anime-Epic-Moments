# Стайлгайд: окружение, команды и локальные гейты

## Описание

Этот документ отвечает на вопрос «**как настроить рабочее место и какими командами пользоваться**» в
проекте **Anime Epic Moments**: установка инструментов, управление зависимостями через **uv**, запуск
приложения и тестов, обязательные гейты перед коммитом, базовый git-процесс.

**Для кого:** каждый разработчик; читать первым вместе с [onboarding.md](onboarding.md).

Правила написания кода (слои, нейминг, async, ошибки, коммиты, PR, review) вынесены в отдельный
обязательный регламент — [contribution-guide.md](contribution-guide.md). Здесь они не дублируются.
Архитектурные соглашения — в [conventions.md](conventions.md).

Все правила этого документа закреплены конфигами репозитория (`pyproject.toml`, `ruff.toml`,
`.github/workflows/ci.yml`) или являются обязательными практиками.

## Как это работает

### Инструменты

Проект использует **uv** как единый инструмент управления Python и зависимостями. `pip`,
`requirements.txt` и `venv` **не используются** — не добавляйте requirements-файлы и не ставьте
пакеты через pip.

Установка uv (один раз, локально):

```powershell
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Минимальная версия uv зафиксирована в `pyproject.toml`: `[tool.uv] required-version = ">=0.10"`.

### Виртуальное окружение и зависимости

- Окружение создаётся и обновляется командой `uv sync`: она создаёт `.venv`, ставит зависимости и
  dev-группы.
- Состав зависимостей описан только в `pyproject.toml`:
  - `[project] dependencies` — рантайм (FastAPI, SQLAlchemy 2.x, dishka, Alembic, Redis-клиент и др.);
  - `[dependency-groups] dev` — pytest, pytest-asyncio, pytest-cov, ruff;
  - `[dependency-groups] lint` — import-linter, grimp;
  - `[tool.uv] default-groups = ["dev", "lint"]` — обе группы ставятся по умолчанию.
- `uv.lock` закоммичен. Вручную его не правят — только через `uv lock` / `uv add`.
- Новая зависимость: `uv add <пакет>` (варианты: `--dev`, `--group lint`). Команда обновляет и
  `pyproject.toml`, и `uv.lock` одновременно.
- Изменение зависимостей **должно** идти в одном коммите со свежим `uv.lock`, иначе
  `uv sync --frozen` упадёт в CI.

### Команды

Windows (PowerShell) / Linux-macOS (bash):

| Действие                  | Windows (PowerShell)                                     | Linux / macOS (bash)                                        |
|---------------------------|-----------------------------------------------------------|-------------------------------------------------------------|
| Установить окружение      | `uv sync`                                                 | `uv sync`                                                    |
| Обновить окружение        | `uv sync --frozen`                                        | `uv sync --frozen`                                           |
| Запустить приложение      | `$env:PYTHONPATH="src"; uv run python -m backend.main`    | `PYTHONPATH=src uv run python -m backend.main`               |
| Тесты (с coverage)        | `uv run pytest`                                           | `uv run pytest`                                              |
| Быстрые тесты             | `uv run pytest -q --no-cov`                               | `uv run pytest -q --no-cov`                                  |
| Линт                      | `uv run ruff check src tests`                             | `uv run ruff check src tests`                                |
| Проверка формата          | `uv run ruff format --check src tests`                    | `uv run ruff format --check src tests`                       |
| Автоформат                | `uv run ruff format src tests`                            | `uv run ruff format src tests`                               |
| Границы слоёв             | `$env:PYTHONPATH="src"; uv run lint-imports`              | `PYTHONPATH=src uv run lint-imports`                         |
| Миграции (Alembic)        | `uv run alembic -c build/alembic/alembic.ini upgrade head`| `uv run alembic -c build/alembic/alembic.ini upgrade head`   |
| Новая миграция            | `uv run alembic -c build/alembic/alembic.ini revision --autogenerate -m "<msg>"` | то же |

Сокращения продублированы в `Makefile` (`make install`, `make lint`, `make test-fast`,
`make check-imports`, `make docker-run`, ...) — на Windows цели Makefile выполняются через WSL/Git Bash.

Приложение поднимается на `APP_HOST:APP_PORT` из `.env` (по умолчанию `http://127.0.0.1:5000`);
Swagger UI доступен на `/docs`.

### Первый запуск

1. Создай `.env` из примера и заполни значения:

   ```powershell
   Copy-Item .env.example .env
   ```

   ```bash
   cp .env.example .env
   ```

2. Подними инфраструктуру (Postgres + Redis) локально, если нет своей:
   `docker compose -f docker-compose.yml up -d postgres redis` (подробности —
   [deployment/overview.md](deployment/overview.md)).
3. `uv sync` — установить зависимости.
4. Примени миграции: `uv run alembic -c build/alembic/alembic.ini upgrade head`
   (или включи `DATABASE_AUTO_INIT=1` — таблицы создадутся автоматически).
5. Запусти приложение (команда из таблицы выше), проверь `GET /health` и `/ready`.
6. Прогони тесты: `uv run pytest -q --no-cov`. Если всё зелёное — окружение готово.

Типичные проблемы первого запуска:

| Симптом                                   | Причина и решение |
|-------------------------------------------|-------------------|
| `SECRET_KEY is not set` / ошибка настроек  | не создан `.env` — скопируй из `.env.example` и заполни минимум `SECRET_KEY`, `DATABASE_URL` |
| `can't connect to Postgres`                | БД не поднята: запусти compose-сервисы или поправь `DATABASE_URL` |
| `lint-imports: package 'backend' not found`| забыла/забыл `PYTHONPATH=src` перед командой |
| Тесты падают на Redis                      | Redis опционален: убедись, что `REDIS_ENABLED` соответствует окружению, либо подними redis из compose |
| Порт 5000 занят                            | поменяй `APP_PORT` в `.env` |

### Локальные гейты перед коммитом

Эти четыре команды должны проходить без ошибок — CI прогоняет ровно их же:

```powershell
uv run ruff check src tests
uv run ruff format --check src tests
$env:PYTHONPATH="src"; uv run lint-imports
uv run pytest -q --no-cov
```

```bash
uv run ruff check src tests && \
uv run ruff format --check src tests && \
PYTHONPATH=src uv run lint-imports && \
uv run pytest -q --no-cov
```

Полный тестовый прогон с coverage (`uv run pytest`) полезен перед PR: отчёт показывает
непокрытые строки (`term-missing`). Coverage по ветвям включён (`[tool.coverage.run] branch = true`).

### Git-процесс (базово)

- `main` — стабильная ветка. Работа ведётся в ветках `feature/<имя>`, `fix/<имя>` и вливается
  через pull request (в solo-режиме допускается прямой merge при зелёных гейтах).
- Перед коммитом проверяй `git status` и `git diff` — коммитится только то, что ты видел.
- Не коммить: `.env`, секреты, артефакты (`__pycache__`, кэши тестов), большие бинарники.
  Всё лишнее уже в `.gitignore`; секреты в коде/конфигах запрещены — в `.env.example` только заглушки.
- Формат сообщений коммитов, атомарность, шаблон PR, правила review и полный цикл работы над
  фичей описаны в [contribution-guide.md](contribution-guide.md) (разделы 3–7) — там же чеклисты.

## Почему это сделано так

- **Один инструмент (uv)** вместо связки pip+venv+pip-tools: быстрые установки, детерминированный
  lock-файл, единые команды для CI и локальной машины.
- **Гейты локально = гейты в CI**: невозможно «у меня всё проходит», а потом красный билд.
- **Команды даны сразу для PowerShell и bash**: проект разрабатывается на Windows, а CI крутится на
  ubuntu-latest — обе среды равноправны.
- **Код-стайл вынесен в contribution-guide**: правила кода меняются чаще окружения, и им нужен один
  дом без расползания по двум документам.

## Где в коде

- `pyproject.toml` — версии Python/uv, зависимости, группы, конфиг pytest, import-linter, coverage
- `ruff.toml` — линт и форматирование (детальный разбор правил — [contribution-guide.md](contribution-guide.md))
- `.github/workflows/ci.yml` — job `quality`: те же гейты, что и локально
- `Makefile` — сокращения команд
- `Dockerfile`, `docker-compose.yml`, `scripts/entrypoint.sh` — упаковка и запуск
- `.env.example` — заглушки всех переменных окружения с комментариями
- `docs/contribution-guide.md` — требования к коду, коммитам, PR и процессу разработки

## Связанные документы

- [Contribution Guide](contribution-guide.md) — код, коммиты, PR, review
- [Онбординг](onboarding.md)
- [Конвенции](conventions.md)
- [Деплой](deployment/overview.md)
- [Тестовая стратегия](testing/strategy.md)
- [Хаб документации](README.md)
