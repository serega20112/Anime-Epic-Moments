# Contribution Guide: требования к коду, коммитам, Pull Request'ам и процессу разработки

## Описание

Этот документ — **обязательный регламент** разработки в **Anime Epic Moments**. Он отвечает на вопросы:

- как писать код (слои, нейминг, async, ошибки, логирование, конфигурация);
- какой стиль кода считается правильным и чем он закреплён;
- как оформлять коммиты и Pull Request'ы;
- как проходит code review;
- как выглядит полный цикл работы над фичей или багом.

**Для кого:** каждый, кто коммитит в репозиторий. Новичкам читать целиком перед первым PR (совместно
с [onboarding.md](onboarding.md)), опытным участникам — использовать как справочник.

**Когда читать:** перед первым коммитом — разделы 1–3; перед первым PR — разделы 4–7.

Правила окружения и команд (`uv sync`, локальные гейты) описаны в [styleguide.md](styleguide.md) — Архитектурные
соглашения без процессной части — в [conventions.md](conventions.md).

---

## Как это работает

### 1. Требования к коду

#### 1.1. Слои и границы импортов

Слои приложения и направление зависимостей закреплены контрактом import-linter `Layer Boundaries`
(`pyproject.toml` → `[tool.importlinter]`):

```
layers = ["presentation", "infrastructure", "application", "domain"]
```

В import-linter верхний слой может импортировать нижележащие. Разрешения:

| Слой             | Может импортировать                 | Не может импортировать       |
|------------------|-------------------------------------|------------------------------|
| `presentation`   | infrastructure, application, domain | —                            |
| `infrastructure` | application, domain                 | presentation                 |
| `application`    | domain                              | presentation, infrastructure |
| `domain`         | ничего из слоёв проекта             | все остальные слои           |

Жёсткие запреты сверх таблицы:

- **domain не знает о FastAPI, SQLAlchemy, Redis, HTTP-клиентах.** Никаких `from fastapi ...`,
  `from sqlalchemy ...`, `import jwt`, `import redis` в `src/backend/domain/`.
- **infrastructure не знает о presentation.** Репозиторий не может возвращать/принимать
  `Request`, `Response`, Pydantic-схемы роутов.
- Порты (интерфейсы репозиториев, внешних сервисов и UoW) объявляются в `application/interface/`
  (`repositories/`, `services/`, `unit_of_work.py`); реализации — в `infrastructure/repositories/`,
  `infrastructure/external/` и т.д. Application-код зависит только от портов. Домен портов не содержит.
- DI-проводка (кто кого получает) живёт только в `infrastructure/di/providers/`.

Нарушение ловится автоматически: `$env:PYTHONPATH="src"; uv run lint-imports` (Windows) /
`PYTHONPATH=src uv run lint-imports` (Unix). Гейт обязателен локально и в CI.

Типичные нарушения границ (антипримеры, которые ловит lint-imports):

```python
# ПЛОХО: domain импортирует инфраструктуру
# src/backend/domain/highlight/service.py
from sqlalchemy.ext.asyncio import AsyncSession  # нарушение: domain -> infrastructure

# ПЛОХО: application импортирует presentation
# src/backend/application/use_cases/watch/get_watch_page.py
from fastapi import Request  # нарушение: application -> presentation

# ПЛОХО: infrastructure импортирует presentation
# src/backend/infrastructure/repositories/user_repository.py
from backend.presentation.api.requests.auth_mapper import

...  # нарушение
```

Если кажется, что правило мешает — это сигнал неверной декомпозиции: перенесите интерфейс в domain или DTO в
application, а не отключайте контракт.

#### 1.2. Naming conventions

| Что                            | Правило                                    | Пример                                         |
|--------------------------------|--------------------------------------------|------------------------------------------------|
| Use case класс                 | `<Действие><Сущность>UseCase`              | `CreateHighlightUseCase`                       |
| Файл use case                  | snake_case глагольная фраза                | `create_highlight.py`                          |
| Каталог use cases              | по доменной сущности                       | `use_cases/highlight/`                         |
| Command-DTO (вход use case)    | `<Действие><Сущность>Command`              | `CreateHighlightCommand`                       |
| Result-объект (выход use case) | `<Сущность>Result`                         | `HighlightResult`                              |
| Query-DTO на чтение            | `<Сущность><Запрос>`                       | `AnimeSearchQuery`                             |
| Интерфейс репозитория          | `<Сущность>Repository`                     | `HighlightRepository` (`application/interface/repositories/`) |
| Реализация репозитория         | то же имя в `infrastructure/repositories/` | `HighlightRepository`                          |
| Интерфейс внешнего сервиса     | `<Что>Interface`                           | `RecommendationServiceInterface`               |
| Доменная сущность              | существительное                            | `Highlight`, `User`                            |
| Value object                   | существительное                            | `Email`, `HighlightCategory`                   |
| Политика                       | `<Сущность>Policy`                         | `HighlightPolicy`                              |
| Файл роутов                    | `<зона>_route.py`                          | `highlight_route.py`                           |
| Роутер                         | `<зона>_router`                            | `highlight_router`                             |
| Имя маршрута (`name=`)         | `<зона>.<действие>`                        | `highlight.create_highlight`                   |
| SQLAlchemy-модель              | `<Сущность>Model`                          | `HighlightModel`                               |
| Таблица                        | множественное число, snake_case            | `highlights`, `user_follows`                   |
| Тест                           | `test_<что_тестируем>.py`                  | `test_create_highlight.py`                     |

#### 1.3. Async/await правила

- Весь IO (БД, сеть, файлы, кэш) — только `async`. Синхронных блокирующих вызовов (`requests`, `time.sleep`,
  sync-драйвер БД) в рантайм-коде быть не должно. Исключение — утилиты вне запроса; новое сетевое API подключать через
  `httpx.AsyncClient`.
- Метод use case называется `execute` и принимает command/query-DTO, а не «россыпь» аргументов:
  `async def execute(self, command: CreateHighlightCommand) -> HighlightResult`.
- Транзакция — через `UnitOfWorkInterface`: `async with self.unit_of_work:` оборачивает одну бизнес-операцию (см.
  `create_highlight.py`).
- В тестах pytest-asyncio работает в режиме `asyncio_mode = "auto"`: обычные `async def test_...`
  без декораторов.
- CPU-тяжёлые операции в event loop не выполняем: выносить в executor либо пересматривать подход.

#### 1.4. Обработка ошибок

Иерархия доменных ошибок — `src/backend/domain/exceptions.py`:

```
DomainError
├── NotFoundError          # ресурс не найден
├── ValidationError        # данные не прошли валидацию
├── AuthenticationError    # аутентификация не прошла
├── AuthorizationError     # нет прав
├── DuplicateError         # дубликат ресурса
└── ExternalServiceError   # сбой внешнего API/сервиса
```

Правила:

1. Ошибки предметной области — свои классы, наследники `DomainError`. Голый `Exception`,
   `ValueError`, `RuntimeError` в домене/application запрещены для новых ошибок.
2. В domain нельзя поднимать FastAPI-исключения (`HTTPException`) — HTTP это деталь транспорта.
3. Перевод доменных ошибок в HTTP-ответы происходит в presentation (роут/handler), а не в домене.
4. Успешный, но «отрицательный» исход бизнес-правила (лимит превышен, спойлер-фильтр сработал)
   оформляется Result-объектом (`HighlightResult.failure(...)`), а не исключением — так use case остаётся читаемым, а
   вызывающий код получает статус и сообщение явно.

Известный долг (не копировать в новый код):

- `domain/aggregates/user/exceptions.py` (`InvalidEmailError`, `InvalidUsernameError`) наследуются от
  голого `Exception`, а не от `DomainError`; аналогичный локальный `InvalidHighlightTimeError`
  объявлен прямо в `aggregates/highlight/highlight.py`. При касании этих файлов переносите их в общую
  иерархию.
- Часть use cases возвращает Result со встроенным `status_code` (HTTP-утечка в application). Для новых use cases
  предпочтителен нейтральный Result без HTTP-кодов; перевод в статусы — на слое presentation.

#### 1.5. Логирование

- Единый логгер: `logging.getLogger("anime_epic_moments")`.
- Формат сообщений — ключ=значение: `logger.info("request_finished method=%s path=%s status=%s duration_ms=%s", ...)`.
  Это требование: сообщения парсятся и экспортируются в JSON (`python-json-logger`).
- Контекст запроса доступен везде через contextvars `request_id_var`, `user_id_var`
  (`backend/utils/logging.py`); middleware проставляет их до обработки и чистит после.
- Уровни: `DEBUG` — диагностика, `INFO` — факты жизненного цикла (старт/финиш запроса),
  `WARNING` — отклонённые токены/CSRF/413, `ERROR`+`exc_info=True` — необработанные исключения.
- Логировать секреты (токены, пароли, cookies, письма пользователей) запрещено.

#### 1.6. Конфигурация

- Все настройки — через класс `backend.config.Settings`; значения читаются функциями из
  `backend/config/sections/*` при загрузке модуля. Прямое `os.getenv(...)` в бизнес-коде запрещено.
- Новый параметр окружения — три обязательных шага в одном PR:
    1. функция чтения + значение по умолчанию в `src/backend/config/sections/<зона>.py`;
    2. атрибут в `src/backend/config/settings.py`;
    3. строка с русским комментарием в `.env.example` (только заглушки, никаких реальных значений).
- Секреты попадают только из `.env` / окружения. Коммитить `.env` или реальные ключи — блокирующая ошибка.

#### 1.7. Запрещённые практики (краткий свод)

| Запрещено                                                    | Как правильно                                                  |
|--------------------------------------------------------------|----------------------------------------------------------------|
| Бизнес-логика в route-хендлерах                              | route → маппер → use case → Result                             |
| Прямой SQL / `AsyncSession` в use cases                      | методы репозитория из `application/interface/repositories`                    |
| `HTTPException` в application/domain                         | доменные ошибки / Result                                       |
| `os.getenv` вне `config/sections`                            | `Settings.<параметр>`                                          |
| Секреты в коде, конфигах, тестах                             | окружение + заглушки в `.env.example`                          |
| pip / requirements.txt                                       | `uv add <пакет>` + обновлённый `uv.lock`                       |
| `import *`                                                   | явные импорты (F403/F405)                                      |
| Отключение правил ruff/import-linter per-file без обсуждения | обсудить в PR/issue                                            |
| `datetime.utcnow()` в новом коде                             | `datetime.now(UTC)` (устарел в 3.12; в кодовой базе есть долг) |

#### 1.8. Примеры «хорошо / плохо» для типичных задач

**Новый use case.**

Хорошо (паттерн `CreateHighlightUseCase`, `application/use_cases/highlight/create_highlight.py`):

```python
class CreateHighlightUseCase:
    """Use case для создания Highlight."""

    def __init__(self, repo: HighlightRepository, unit_of_work: UnitOfWorkInterface): ...

    async def execute(self, command: CreateHighlightCommand) -> HighlightResult:
        """Create a highlight within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: CreateHighlightCommand) -> HighlightResult:
        if not await HighlightPolicy.can_add_highlight(command.user_id, command.highlights_this_hour):
            return await HighlightResult.failure("Превышен лимит", status_code=403)
        highlight = Highlight(...)
        result = await self.repo.add(highlight)
        return await HighlightResult.success(result, status_code=201)
```

Признаки «хорошо»: зависимости через конструктор (интерфейсы из domain), проверка политики — доменным `HighlightPolicy`,
инварианты — в конструкторе сущности `Highlight`, транзакция — UoW, инвалидация кэшей после записи.

Плохо:

```python
class HighlightCreator:  # имя вне конвенции
    def __init__(self):
        from backend.infrastructure.files.database import get_session  # скрытая зависимость + слой
        self.session = asyncio.run(get_session())  # sync-вызов async

    def create(self, user_id, anime_id, start, end):  # «россыпь» аргументов
        if end <= start:
            raise HTTPException(status_code=400)  # HTTP в application
        session.execute(text("INSERT INTO highlights ..."))  # SQL мимо репозитория
```

**Новый endpoint.**

Хорошо (паттерн `presentation/api/v1/*.py`):

```python
@items_router.post("/", name="highlight.create_highlight")
async def create_highlight(
        request: Request,
        form: Annotated[CreateHighlightForm, Depends(CreateHighlightForm.as_form)],
        highlight_use_case: FromDishka[CreateHighlightUseCase],
):
    user = request.state.user  # пользователь уже загружен middleware
    if user is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    result = await highlight_use_case.execute(map_to_command(user.id, form))
    return build_response(result)  # JSON или HTML в зависимости от wants_json
```

Плохо:

```python
@app.post("/api/highlight")  # мимо роутера зоны, нет name=
def create(request: Request):  # sync-хендлер с IO
    data = request.json()  # валидация руками вместо Pydantic/Form
    db = SessionLocal()  # своя сессия в обход DI/UoW
    db.execute(...)  # SQL в presentation
```

Чек-лист нового endpoint: роутер зоны + `name=`, auth через `request.state.user`, делегирование use case из DI
(`FromDishka[...]`), JSON/HTML ветки, обработка доменных ошибок, тесты (unit на use case + integration на роут),
обновление [api/endpoints.md](api/endpoints.md).

**Изменение модели данных.**

Порядок обязательный: домен (entity/value object) → SQLAlchemy-модель в
`infrastructure/models/<зона>/` → миграция Alembic → тест репозитория
(`tests/integration/infrastructure/repositories/`) → при необходимости правки
`docs/database/schema.md`.

Миграция: `uv run alembic -c build/alembic/alembic.ini revision --autogenerate -m "add xxx"`, проверить сгенерированный
файл вручную (autogenerate ошибается на rename), затем
`... upgrade head` локально. Миграция коммитится вместе с изменением модели — отдельным коммитом в том же PR.

### 2. Стиль кода и инструменты

#### 2.1. ruff

Конфиг — `ruff.toml`: `target-version = "py312"`, `line-length = 100`, кавычки двойные.

Включены наборы: `E` (ошибки pycodestyle), `W` (предупреждения pycodestyle), `F` (pyflakes),
`I` (isort-сортировка импортов), `N` (pep8-naming), `D` (pydocstyle, convention = google),
`UP` (pyupgrade).

Отключённые правила и почему:

| Правило                         | Значение                             | Статус                                                                                                                 |
|---------------------------------|--------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| `D100/D104/D107`                | docstring модулей/пакетов/`__init__` | отключено постоянно — необязательно                                                                                    |
| `D101/D102/D103`                | docstring классов/методов/функций    | **долг**: выключено ради старого кода, но новый публичный код обязан иметь docstrings (Google: summary, Args, Returns) |
| `E501`                          | длина строки                         | **долг**: держим строки ≤ ~100 символов; контролируют format + review                                                  |
| `D203/D212/D213/D401/D413/D415` | стилевые конфликты pydocstyle        | отключено постоянно, чтобы зафиксировать один стиль                                                                    |
| F401 в `__init__.py`            | переэкспорты                         | осознанное разрешение                                                                                                  |
| `D` в `tests/**`                | docstrings в тестах                  | необязательны                                                                                                          |

Отключать правила точечно (per-file-ignores, `# noqa`) можно только после обсуждения в PR — молчаливые обходы запрещены.

#### 2.2. Типизация

- mypy/pyright **не настроены** (осознанно). Это значит: типы не проверяет CI — их проверяет reviewer. Аннотации
  обязательны для всех публичных сигнатур (функции, методы, атрибуты классов).
- Современный синтаксис: `str | None` (не `Optional[str]`), `list[str]` (не `List[str]`),
  `collections.abc.Callable/Iterable` — набор `UP` частично страхует.
- Возвращаемые типы use cases и методов репозиториев — конкретные (DTO/сущности), не `dict`.

#### 2.3. Форматирование и docstrings

- Перед коммитом: `uv run ruff format src tests` (форматтер — источник истины по пробелам, переносам, кавычкам).
- Docstrings обязательны для новых публичных модулей, классов, методов — стиль Google:
  первая строка — краткое summary (точка в конце допустима), далее `Args:` / `Returns:` /
  `Yields:` где применимо. Частные `_методы` — по необходимости.
- Комментарии — только там, где код сам себя не объясняет (нетривиальный алгоритм, внешний контракт, workaround с
  причиной). Комментарии-пересказ кода удаляются.

### 3. Коммиты

#### 3.1. Формат

Проект использует упрощённый Conventional Commits:

```
<тип>: <описание в повелительном наклонении>
```

Типы: `feat` (новая функциональность), `fix` (исправление бага), `refactor` (изменение кода без смены поведения), `docs`
(документация), `test` (тесты), `chore` (сборка, зависимости, конфиги),
`ci` (CI/CD), `update` (правка недавнего собственного изменения).

Описание — с маленькой буквы, без точки в конце; язык русский (допустим английский, если термин точно передаёт смысл).

Breaking change помечается `!` после типа: `feat!: перевести сессии на refresh-токены` — и требует абзац-пояснение в
теле коммита.

#### 3.2. Правила

- Один коммит — одна логическая единица: фича, фикс, чистка формата. Смешивать `refactor` и поведение в одном коммите
  нельзя — иначе невозможно найти регресс через `git bisect`.
- Форматирование (`ruff format`) — отдельным коммитом, не примешивать к логике.
- Изменение зависимостей всегда идёт в одном коммите с `uv.lock` (`uv add` обновляет его сам).
- Перед коммитом: `git status` и `git diff` — коммитится только то, что вы видели.
- **Никогда не коммитить:** `.env` и любые секреты (API-ключи, SMTP-пароли, CORS с внутренними хостами), артефакты
  (`__pycache__`, `.pytest_cache`), большие бинарники, `uv.lock` без изменений в `pyproject.toml`, временные
  скрипты-«однодневки».

#### 3.3. Примеры

Хорошие:

```
feat: добавить лимит хайлайтов для гостей
fix: пропускать primary LLM без API-ключа
fix: инвалидировать профиль-кэш после смены username
refactor: вынести security-helpers из app_factory в отдельный модуль
docs: описать flow регистрации в api/endpoints.md
test: покрыть SetHighlightLikeUseCase случаем повторного лайка
chore: поднять fastapi до 0.116.1
```

Плохие (реальный долг истории репозитория — так больше не делаем):

```
refactoring            # что именно изменено?
fixes                  # какие фиксы?
[AEM-async-version] add and fix: refactoring and adding new providers   # мусор в префиксе, всё сразу
update                 # без содержания
wip                    # незавершённая работа не попадает в main
```

#### 3.4. Коммиты по типам работ

- **Фича:** серия мелких коммитов (`feat: ...` + `test: ...` + `docs: ...`) или один цельный — допустимо и то и другое;
  главное — атомарность и зелёные гейты на вершине ветки.
- **Рефакторинг:** сначала коммит с тестами, фиксирующими текущее поведение, потом рефакторинг.
- **Миграция БД:** коммит «модель + автогенерированная миграция + тест репозитория» отдельно от коммита с логикой,
  использующей новое поле.
- **Фикс бага:** коммит содержит фикс и регрессионный тест; в описании PR — шаги воспроизведения.

### 4. Pull Request'ы

#### 4.1. Ветки

- `feature/<краткое-имя>` — новая функциональность; `fix/<краткое-имя>` — багфиксы;
  `chore/<...>`, `docs/<...>` — обслуживание и документация.
- Ветка от актуального `main`; имя — латиница, дефисы, без номеров тикетов внутри имени (номер указывается в описании
  PR).

#### 4.2. Шаблон описания PR (обязателен)

Шаблона GitHub пока нет (долг) — описание оформляется руками по структуре:

```markdown
## Что и зачем

<1–3 предложения: проблема/фича и мотивация. Ссылка на issue, если есть.>

## Что сделано

- <ключевые пункты изменений>

## Как тестировалось

<Команды, сценарии, окружение. Для UI — скриншот/видео.>

## Документация

<Какие docs/*.md обновлены или «изменения не требуются, потому что ...».>

## Checklist

- [ ] Локальные гейты зелёные (ruff check / format / lint-imports / pytest)
- [ ] Добавлены/обновлены тесты
- [ ] Нет секретов и мусора в diff'е
- [ ] Документация обновлена там, где нужно
```

#### 4.3. Размер и состав

- Ориентир: **≤ ~400 изменённых строк** и ≤ ~15 файлов на PR. Крупные работы дробите на цепочку PR (каркас →
  наполнение → чистка).
- Каждый PR содержит код + тесты + документацию одним набором: PR без тестов на новую логику не принимается.
- Draft PR — когда работа в процессе, но нужна ранняя обратная связь по подходу или CI-прогон. Draft переводится в Ready
  только при зелёном CI и заполненном описании.

#### 4.4. CI и обновление PR

- CI (`.github/workflows/ci.yml`) прогоняет те же 4 гейта, что и локально: `ruff check`,
  `ruff format --check`, `lint-imports`, `pytest -q --no-cov` на Python 3.12 / ubuntu-latest. Merge возможен только при
  полностью зелёном CI.
- После замечаний reviewer'а: preferred-flow — `git rebase main` + force-push-with-lease в свою ветку PR (история
  остаётся линейной и читаемой). Merge-commit в ветку PR допускается, если rebase опасен (давняя долгоживущая ветка).
- Force-push без `--lease` и перезапись чужих веток запрещены. После force-push предупреждайте в комментариях PR
  («rebase done»).
- Squash-merge не используется по умолчанию: история коммитов ветки сохраняется; если в ветке накопился шум (`wip` и
  пр.) — почистить интерактивным rebase до ревью.

### 5. Code Review

#### 5.1. Что обязан проверить reviewer

1. **Границы слоёв** — нет утечек (FastAPI/SQLAlchemy в домене, HTTP в application); `lint-imports`
   зелёный, но глазом проверяется семантика (например, Result с `status_code` в application).
2. **Тесты:** новая логика покрыта unit; граничные зависимости — integration; тесты проверяют поведение, а не реализацию
   (моки только на границах).
3. **Безопасность:** нет секретов; новые эндпоинты учитывают auth (`request.state.user`), CSRF, rate-limit там, где
   аналогичные эндпоинты его имеют.
4. **Производительность:** N+1 запросов, отсутствие индексов под новые выборки, синхронные блокировки в async-коде.
5. **Стиль:** аннотации типов, docstrings, отсутствие закомментированного кода и `print`.
6. **Документация:** затронутые `docs/*.md` обновлены; команды и пути в них актуальны.

#### 5.2. Процесс и сроки

- Review запрашивается сразу после открытия PR; целевое время первого ответа — **один рабочий день**.
- Замечания формулируются конкретно и с обоснованием («здесь N+1: на 100 хайлайтов будет 101 запрос — предлагаю
  `selectinload`»), а не «мне не нравится». Вопросы — префиксом `?`; необязательные предложения — `nit:`.
- Автор не спорит ради спора: если не согласен — приводит аргумент в треде; при тупике вопрос выносится на обсуждение
  команды/в issue.
- **Approve:** гейты зелёные, замечания уровня «блокер» отсутствуют. **Request changes:** есть хотя бы одно блокирующее
  замечание (безопасность, границы, отсутствие тестов, регресс поведения). Мелкие `nit` не блокируют approve — автор
  вправе исправить их в том же PR или следующим.

### 6. Процесс разработки фичи / бага

Полный цикл:

```
issue → ветка feature/fix → код + тесты + docs → локальные гейты → PR → review → merge в main
```

1. **Issue** — любая нетривиальная работа начинается с issue (что, зачем, критерии готовности). Мелкий очевидный фикс
   допустим без issue, но описание PR тогда несёт всю мотивацию.
2. **Ветка** — свежий `main`, имя по п. 4.1.
3. **Код + тесты + документация.** Обновление документации обязательно в том же PR, если меняются:
   публичное HTTP API ([api/endpoints.md](api/endpoints.md)), схема БД ([database/schema.md](database/schema.md)),
   доменные правила ([domain/core.md](domain/core.md)), безопасность ([security/security.md](security/security.md)),
   процесс/команды ([styleguide.md](styleguide.md), этот гайд). Правило простое: если поведение задокументировано — доку
   правишь тем же PR.
4. **Локальные гейты** (те же, что в CI):
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
5. **PR** по шаблону п. 4.2, зелёный CI.
6. **Review** по разделу 5; после approve — merge автором.
7. После merge: удалить ветку, проверить, что issue закрыт; если изменение пользовательское — упомянуть его в release
   notes следующего релиза.

**Когда нужна миграция Alembic:** любое изменение схемы (таблицы, колонки, индексы, ограничения). Оформление:
autogenerate → ручная проверка файла → `upgrade head` локально → миграция в том же PR. Обратную совместимость для
zero-downtime деплоя сейчас можно не обеспечивать (одноинстансовый деплой, окно простоя допустимо) — но миграция вниз
(`downgrade`) должна существовать.

**Работа с technical debt:** долг чинится маленькими PR «вслед за касанием»: тронули файл с долгом — исправьте долг в
нём, если это не раздувает PR. Крупный долг (compat-слой в `tests/conftest.py`, Result с HTTP-кодами, legacy
`auth_required`) фиксируется в issue и не размазывается по фичевым PR. Известный реестр долга ведётся в конце
соответствующих документов (см. «Почему это сделано так» и разделы «Ограничения»).

### 7. Чеклисты

**Перед созданием PR:**

- [ ] Ветка свежая, история читаемая (нет `wip`/`fixup`, либо они сквошнуты).
- [ ] `ruff check`, `ruff format --check`, `lint-imports`, `pytest -q --no-cov` — зелёные локально.
- [ ] Новая логика покрыта тестами; маркер соответствует уровню (unit/integration/e2e).
- [ ] Изменения схемы БД сопровождаются миграцией и тестом репозитория.
- [ ] Новые переменные окружения добавлены в `config/sections`, `settings.py`, `.env.example`.
- [ ] Затронутая документация обновлена; ссылки в ней рабочие.
- [ ] `git diff` просмотрен глазами; секретов и мусора нет; `uv.lock` согласован с `pyproject.toml`.
- [ ] Описание PR заполнено по шаблону п. 4.2.

**Чеклист reviewer'а:**

- [ ] Границы слоёв: домен чист, application без HTTP, infrastructure без presentation.
- [ ] Нейминг по таблице п. 1.2; use case — `execute(Command) -> Result`, зависимости через DI.
- [ ] Ошибки: доменные классы/Result; никаких голых `Exception` и `HTTPException` ниже presentation.
- [ ] Async: нет блокирующего IO; транзакции через UoW; кэши инвалидируются после записей.
- [ ] Безопасность: auth/CSRF/rate-limit на новых мутирующих эндпоинтах; секретов в diff нет.
- [ ] Тесты проверяют поведение; маркеры корректны; coverage не просел.
- [ ] Документация согласована с кодом.
- [ ] Вердикт явный: approve или request changes (с перечнем блокеров).

**После merge:**

- [ ] Ветка удалена (локально и на сервере).
- [ ] Issue закрыт/обновлён; решение зафиксировано, если обсуждались альтернативы.
- [ ] Пользовательское изменение отражено в release notes.
- [ ] Если PR трогал прод-конфиги/env — деплой-инструкция обновлена ([deployment/overview.md](deployment/overview.md)).

---

## Почему это сделано так

- **Односторонние зависимости слоёв** позволяют менять инфраструктуру (Postgres → другая БД, Gemini → другой LLM) без
  единого изменения в домене; import-linter превращает это правило из «джентльменского соглашения» в падающий билд.
- **Упрощённый Conventional Commits** (не строгая спецификация) выбран сознательно: префикс типа + человеческое описание
  на русском дают пользу для changelog и `git log`, не создавая бюрократию. История репозитория показывает, что без
  жёсткого правила появляются «refactoring» и «fixes» — поэтому формат обязателен, а старые коммиты считаются долгом, а
  не образцом.
- **Одинаковые гейты локально и в CI** убирают класс «работает у меня»; список гейтов короткий (4 команды) специально,
  чтобы их реально запускали.
- **Ограничение размера PR** следует из практики review: качество проверки падает после ~400 строк; лучше три понятных
  PR, чем один «всё включено».
- **Статические типы без mypy** — компромисс: аннотации дают документацию и подсказки IDE, но настройка строгого чекера
  на legacy-коде потребовала бы недели чисток. Решение будет пересмотрено после погашения долга (future improvement).
- **Долг зафиксирован письменно**, а не замалчивается: у каждого известного отклонения есть статус (долг/осознанное
  решение), чтобы новые участники не копировали антипаттерны.

## Где в коде

- `pyproject.toml` — контракт import-linter (`Layer Boundaries`), конфиг pytest (маркеры,
  `asyncio_mode = auto`), coverage (`branch = true`), группы зависимостей
- `ruff.toml` — линт и формат: включённые наборы E/W/F/I/N/D/UP, отключённые правила долга
- `.github/workflows/ci.yml` — job `quality`: 4 гейта на push/PR в `main`/`master`
- `src/backend/presentation/app_factory.py` — сборка приложения, middleware (logging, security, CSRF), регистрация
  роутеров
- `src/backend/infrastructure/di/` — dishka-контейнер и провайдеры всех use cases
- `src/backend/domain/exceptions.py` — базовая иерархия доменных ошибок
- `src/backend/config/settings.py` + `src/backend/config/sections/` — чтение конфигурации
- `tests/conftest.py` — общие fixtures (`db_session`, `async_db_session`, `flask_app_factory`, ...)
- `Makefile` — сокращения команд (`make lint`, `make test`, ...)
- `build/scripts/entrypoint.sh` — запуск gunicorn + опциональные миграции в контейнере

## Связанные документы

- [Стайлгайд: окружение и команды](styleguide.md)
- [Конвенции](conventions.md)
- [Онбординг](onboarding.md)
- [Архитектура](architecture/overview.md)
- [Тестовая стратегия](testing/strategy.md)
- [API](api/endpoints.md)
- [База данных](database/schema.md)
- [Хаб документации](README.md)
