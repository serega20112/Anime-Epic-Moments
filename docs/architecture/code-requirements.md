# Требования к коду (Code Requirements)

Обязательные правила для всего кода `src/backend`. Каждый пункт проверяется
агентами (`code-review`, `code-fix`) и ревьюерами.

## 1. Конфигурация (Settings)

- Конфиг строится через **pydantic-settings** секциями (`config/app.py`,
  `config/database.py`, ...) и единой точкой `Settings.load()`.
- Секции наследуют `BaseSettings` (образец: `nsi/src/config/base.py`).
- `Settings` регистрируется в Dishka как **APP-синглтон** и принимается через
  конструкторы/`FromDishka`.
- Запрещены прямые импорты `Settings` из presentation, use cases и репозиториев.
- Запрещено вычислять значения конфига на уровне класса при импорте.
- `load_dotenv()` — только в корневом входном точке, не в модулях.

## 2. DI (Dependency Injection)

- Все зависимости — через `FromDishka[...]` + `@inject` (FastAPI-роуты,
  use cases). Запрещён service locator (`container.get(...)` в рантайме).
- Запрещены модульные синглтоны вида `jwt_service = JWTService()`.
- Инфраструктура раскладывается по `di_containers/{base,services,use_cases}.py`;
  точка входа только склеивает контейнер.
- Запрещён неявный контракт через `request.state.*`; вместо него — явные
  типизированные FastAPI-зависимости.

## 3. Границы слоёв Clean Architecture

Направление зависимостей строго однонаправленное:

```
domain -> application -> infrastructure -> presentation (роуты)
```

- **Presentation** не импортирует напрямую инфраструктурные классы
  (репозитории, сервисы, БД). Только application-порты и DI-зависимости.
- **Infrastructure** не делает HTTP-ответов: без `flash()`, `RedirectResponse`,
  `request.app.url_path_for(...)`.
- **Application (use cases)** не знает endpoint-имён, flash-текстов и
  локализованных сообщений. Ошибки — типизированные исключения; presentation
  маппит их в HTTP через словарь `ERROR_STATUS`.

## 4. Порты репозиториев

- Каждый репозиторий реализует ABC-порт из `application/interface/repositories/`
  (generic `ReadRepositoryPort[T, ID, F]` / `WriteRepositoryPort[T, ID]`:
  `get/find_one/find_all/paginate/exists/count/create/update/delete`,
  `PaginatedResult[T]`).
- DI биндит `interface -> реализацию` (`UserRepositoryInterface -> UserRepository`),
  use cases зависят от портов, не от конкретных классов.
- Пагинация/count/exists не дублируются в каждом репозитории вручную.
- Обновление агрегата — `merge`/загрузка в агрегат и сохранение, без
  `select` → перезапись → `flush` (2 запроса + race).

## 5. Unit of Work

- UoW — единственная транзакционная граница: `async with self._uow as uow:`.
- UoW сам открывает транзакцию, коммитит в `__aexit__` при успехе и роллбэчит
  при исключении.
- Репозитории достаются ТОЛЬКО через `uow.repository(...)` внутри границы.
  Передача `AsyncSession` в use case мимо UoW запрещена.
- Порт UoW содержит `__aenter__/__aexit__` и `repository()`.

## 6. База данных и миграции

- Единственный источник схемы — **alembic** (`build/alembic/`).
  Запрещены самодельные `_ensure_*_columns` с сырыми `ALTER TABLE`.
- `init_db(engine)` (create_all) — только dev/test; в проде `verify_schema(engine)`.
- Движок и `sessionmaker` создаются один раз в APP-провайдере Dishka
  (`yield` + `engine.dispose()` на shutdown).
- Запрещены `global engine` / `global SessionLocal`.

## 7. Домен

- Value objects — `@dataclass(frozen=True)` с валидацией в `__post_init__`
  (SystemName, UserID, Timestamp, Email...).
- UI-состояние (`is_liked`, `selected_sort`) — только в presentation-схемах,
  не в домене.
- Мутабельность агрегатов — через методы, сохраняющие инварианты
  (`user.change_email()`), а не публичные поля.
- Фабрики агрегатов: `User.create(...)`, `InformationSystem.create(...)`.
- Время — `datetime.now(timezone.utc)`, не `datetime.utcnow()`.
- Сообщения об ошибках — не на русском в домене; доменные исключения с кодом.

## 8. Use cases

- Зависимости в конструкторе обязательные и типизированные (без
  `service=None` и молча отключаемой логики; при необходимости —
  `NullAccountLockService`).
- Только `uow` и порты; репозитории — через `uow.repository(...)`.
- Фабрики результата — синхронные classmethod'ы без бессмысленного `async`.
- Логирование — декоратором `@application_logging`, не вручную.

## 9. Единый механизм аутентификации

- Одна cookie-схема (`access_token`) через FastAPI-зависимости
  (`Depends(get_current_user)` с `FromDishka[JWTService]`,
  `FromDishka[UserRepository]`).
- Декоратор `auth_required` (заголовок Authorization) — удалить или свести
  к той же схеме.
- `load_user` из middleware — заменить на зависимость; без `container.get` в рантайме.

## 10. Безопасность

- Rate limit по `X-Forwarded-For` — только за доверенным прокси
  (trusted-proxy список из конфига), иначе заголовок спуфится.
- CSP — из конфига, без `'unsafe-inline' 'unsafe-eval'` для script-src;
  поэтапно переходить на nonce.
- Пароль-схема, CSRF-токен и куки — через DI, без двойной регистрации
  (модульный синглтон `csrf_service` + DI-экземпляр = баг).
- Порядок middleware не должен быть хрупким контрактом; состояние —
  через типизированные зависимости.

## 11. HTTP-слой

- JSON API — pydantic-схемы + `response_model`, типизированный `ErrorResponse`
  с кодами (`get_error_model(status)`).
- HTML-формы — маппинг в presentation/schemas через `Form()`-зависимости FastAPI.
- Обработка ошибок — `add_exception_handler` по типам, без эвристики `wants_json`.

## 12. Дубли и легаси

- Один TTL-кэш (`infrastructure/cache/ttl_cache.py`), второй удалить.
- Один alias: `auth_bp = auth_router` — удалить.
- `flask_protection.py` в FastAPI-проекте — переименовать/разрезать:
  rate limit → application/infrastructure, redirect/flash → presentation middleware.
- CSP-строка — из конфига, не захардкожена.

## Чек-лист перед PR

1. Нет импортов `Settings` из presentation/use cases.
2. Нет `container.get(...)` и модульных синглтонов в рантайме.
3. Use case не знает endpoint-имён/flash-текстов; ошибки — исключения.
4. Репозитории наследуют порты; DI биндит интерфейс.
5. Все записи — внутри `async with uow` с коммитом в `__aexit__`.
6. Нет `_ensure_*_columns`; схема только в alembic.
7. VO — frozen dataclass; `datetime.now(timezone.utc)`.
8. Одна схема аутентификации (cookie + FastAPI-зависимости).
9. Rate limit за доверенным прокси; CSP из конфига.
10. Нет дублей (TTL-кэш, auth_bp, csrf_service).