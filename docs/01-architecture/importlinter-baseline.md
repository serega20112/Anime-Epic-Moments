# Baseline нарушений границ слоёв

## Описание

Оба контракта import-linter живут в `pyproject.toml`, но у второго есть список
`ignore_imports`. Документ — карта этого списка: что в нём осталось, почему
каждая строка остаётся и как список поддерживается в актуальном состоянии.

Правила слоёв — в [слоях и правилах](layers-and-rules.md).

## Как это работает

### Контракты

| Контракт | Тип | Что проверяет |
| --- | --- | --- |
| `Layer Boundaries` | `layers` | Порядок `presentation → infrastructure → application → domain`: слой знает только нижележащие |
| `Presentation does not reach Infrastructure` | `forbidden` | Прямой импорт `backend.infrastructure` из `backend.presentation` |

Второй контракт работает с `allow_indirect_imports = true`: проверяются только
прямые импорты. Единственная косвенная цепочка —
`presentation.app_factory → events.lifecycle → infrastructure.database.session`:
`app_factory` подключает lifespan, а lifespan вызывает `init_db` и `verify_schema`.
Транзит через `application` и `domain` уже запрещён контрактом `Layer Boundaries`,
поэтому проверять косвенные пути второй раз нет смысла.

### Текущее состояние

В `ignore_imports` две строки, обе осознанные.

| Модуль назначения | Кто импортирует | Почему остаётся |
| --- | --- | --- |
| `backend.infrastructure.external.video.hls_proxy` | `presentation.api.v1.watch_route.media_proxy` | Ответ проксируемого потока — это HTTP-транспорт: `Request` на входе, `Response` и стриминг на выходе. Порт в `application` описал бы операцию только через HTTP-типы, то есть обменял бы одно нарушение слоя на другое |
| `backend.infrastructure.di.dishka_container` | `presentation.app_factory` | Композиционный корень: собрать контейнер зависимостей может только точка входа приложения. Это исключение не планируется убирать |

Список сокращался поэтапно: шаблоны переехали в `presentation/web`, появились
порты `JWTServiceInterface`, `CSRFServiceInterface`, `TokenBlocklistInterface`,
`RateLimiterInterface`, `ImageStoragePort` и `HealthCheckPort`. Промежуточные шаги
здесь не перечислены: актуален только текущий список из двух строк.

### Как список поддерживается

```bash
uv run python scripts/export_importlinter_baseline.py
```

Скрипт разбирает `src/backend/presentation` через `ast` и печатает готовый блок
`ignore_imports`. Он не импортирует `backend`, поэтому запускается без подготовки
пути импорта. При расхождении скрипт покажет лишние или недостающие строки — их
правят в `pyproject.toml`, а не вручную по памяти.

Проверка контрактов:

```bash
uv run python scripts/check_imports.py
```

Скрипт-обёртка добавляет `src` в путь импорта и вызывает `lint-imports`, поэтому
команда одинаково работает в любой ОС и не требует переменных окружения оболочки.
В CI дополнительно выполняется прямой вызов `lint-imports` с подготовленным
путём.

### Правила ведения

1. Новая строка в `ignore_imports` — только вместе с абзацем обоснования в этом
   документе и упоминанием в ревью.
2. Нарушение вне композиционного корня обязано падать на проверке, а не попадать
   в baseline.
3. Строка удаляется из `pyproject.toml` и из таблицы выше в одном коммите с
   переездом импорта.
4. После правки прогоняются проверка импортов и быстрые тесты.

## Почему это сделано так

- Список вместо отключения контракта: видимые две строки обсуждаются на ревью,
  а отключённый контракт не обсуждается вообще.
- `allow_indirect_imports` выбран, потому что жизненный цикл приложения по природе
  связывает точку входа с инфраструктурой. Запрещать это означало бы добавить
  третий порт ради одной функции запуска.
- Исключение медиа-прокси не устранено, а признано: порт с HTTP-типами перенёс бы
  `fastapi` в прикладной слой, что хуже, чем одна строка baseline.
- Скрипт экспорта написан на `ast`, а не на импорте модулей: статический разбор
  не требует поднятого приложения и работает на этапе линта.

## Где в коде

- `pyproject.toml` — `[tool.importlinter]` и оба контракта
- `scripts/export_importlinter_baseline.py` — генератор списка
- `scripts/check_imports.py` — обёртка над `lint-imports`
- `src/backend/presentation/api/v1/watch_route/media_proxy.py` — исключение медиа-прокси
- `src/backend/presentation/app_factory.py` — композиционный корень
- `src/backend/events/lifecycle.py` — источник косвенной цепочки

## Связанные документы

- [Слои и правила](layers-and-rules.md)
- [Обзор архитектуры](overview.md)
- [DI на Dishka](di-dishka.md)
- [Матрица роутов](route-matrix.md)
- [Соглашения разработки](../04-dev-guide/conventions.md)
