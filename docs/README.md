# Документация AEM

Точка входа в документацию **AEM** (Anime Epic Moments). Здесь описано, кому
какой раздел нужен, кто владеет каждым фактом и как поддерживать документы в
актуальном состоянии.

О проекте в двух предложениях и о запуске — в корневом [README.md](../README.md).
Термины, которые встречаются в документах, собраны в
[глоссарии](00-foundation/glossary.md).

## С чего начать

| Роль | Маршрут чтения |
| --- | --- |
| Заказчик, продукт | [Видение продукта](00-foundation/product-vision.md) → [Глоссарий](00-foundation/glossary.md) |
| Новый разработчик | [Онбординг](04-dev-guide/onboarding.md) → [Слои и правила](01-architecture/layers-and-rules.md) → [Как добавить фичу](04-dev-guide/feature-workflow.md) |
| Автор тестов | [Стратегия тестирования](05-testing/01-testing-strategy.md) → [Unit](05-testing/02-unit-testing.md) → [Integration](05-testing/03-integration-testing.md) → [E2E](05-testing/04-e2e-testing.md) |
| Автор изменений в архитектуре | [Обзор и C4](01-architecture/overview.md) → [Слои и правила](01-architecture/layers-and-rules.md) → [ADR](06-adr/) |
| DevOps, дежурный | [Развёртывание](03-ops/deployment.md) → [Переменные окружения](03-ops/env-reference.md) → [Сопровождение](03-ops/maintenance.md) |
| Работа с провайдерами и поиском | [Провайдеры источников](02-integrations-and-services/providers.md) → [Умный поиск](02-integrations-and-services/llm-search.md) → [Медиа-прокси](02-integrations-and-services/media-proxy.md) |

## Состав разделов

### 00-foundation — базис проекта

| Документ | Содержание |
| --- | --- |
| [glossary.md](00-foundation/glossary.md) | Ubiquitous Language AEM: сокращения, доменные сущности, термины слоёв |
| [product-vision.md](00-foundation/product-vision.md) | Назначение системы, ценность, границы скоупа, пользовательские сценарии |

### 01-architecture — архитектура и границы

| Документ | Содержание |
| --- | --- |
| [overview.md](01-architecture/overview.md) | C4 Context и Container, границы системы, состав контейнеров |
| [layers-and-rules.md](01-architecture/layers-and-rules.md) | Четыре слоя Clean Architecture, DIP, правила импортов, import-linter |
| [domain-model.md](01-architecture/domain-model.md) | Агрегаты, сущности, value objects, политики, порты, доменные ошибки |
| [data-flow.md](01-architecture/data-flow.md) | Жизненный цикл запроса: middleware → сценарий → репозиторий → ответ |
| [di-dishka.md](01-architecture/di-dishka.md) | IoC на Dishka: скоупы APP и REQUEST, провайдеры, правила расширения |
| [data-model.md](01-architecture/data-model.md) | Схема PostgreSQL, ответственность таблиц, инварианты |
| [security.md](01-architecture/security.md) | Аутентификация, CSRF, заголовки, rate limiting, известные пробелы |
| [route-matrix.md](01-architecture/route-matrix.md) | Матрица маршрутов: публичность и проверка владельца |
| [importlinter-baseline.md](01-architecture/importlinter-baseline.md) | Обоснование двух исключений import-linter |

### 02-integrations-and-services — внешний мир и стриминг

| Документ | Содержание |
| --- | --- |
| [providers.md](02-integrations-and-services/providers.md) | Контракты Kodik, AniLibria и остальных провайдеров, ранжирование озвучек |
| [llm-search.md](02-integrations-and-services/llm-search.md) | Умный поиск: цепочка LLM, фолбэк, деградация без ключей |
| [media-proxy.md](02-integrations-and-services/media-proxy.md) | Проксирование HLS, allowlist хостов, перезапись манифестов |

### 03-ops — эксплуатация

| Документ | Содержание |
| --- | --- |
| [env-reference.md](03-ops/env-reference.md) | Полный справочник переменных окружения с типами и значениями по умолчанию |
| [deployment.md](03-ops/deployment.md) | Docker Compose, образ, порты, тома, режимы входа |
| [maintenance.md](03-ops/maintenance.md) | Миграции Alembic, бэкапы PostgreSQL, обслуживание Redis, диагностика |

### 04-dev-guide — разработка

| Документ | Содержание |
| --- | --- |
| [onboarding.md](04-dev-guide/onboarding.md) | Настройка машины, первый запуск, гейты качества |
| [feature-workflow.md](04-dev-guide/feature-workflow.md) | Пошаговое добавление фичи: от сущности до роута |
| [conventions.md](04-dev-guide/conventions.md) | Ruff, типизация, докстринги, обработка ошибок, Conventional Commits |

### 05-testing — канон тестирования

| Документ | Содержание |
| --- | --- |
| [01-testing-strategy.md](05-testing/01-testing-strategy.md) | Пирамида, матрица Unit / Integration / E2E, инструментарий, правила нейминга |
| [02-unit-testing.md](05-testing/02-unit-testing.md) | Чистый домен и сценарии на двойниках, AAA, `ids`, `starlette.status` |
| [03-integration-testing.md](05-testing/03-integration-testing.md) | Связки на реальной PostgreSQL и Redis, откат транзакции, ошибки схемы |
| [04-e2e-testing.md](05-testing/04-e2e-testing.md) | Сквозные пользовательские флоу через `httpx.AsyncClient` |
| [05-fixtures-and-isolation.md](05-testing/05-fixtures-and-isolation.md) | Каскад `conftest.py`, запрет локальных фикстур, защита от утечки контекста |

### 06-adr — Architecture Decision Records

| Запись | Решение |
| --- | --- |
| [0001-clean-architecture.md](06-adr/0001-clean-architecture.md) | Clean Architecture и выделение доменного ядра |
| [0002-dishka-di.md](06-adr/0002-dishka-di.md) | Dishka вместо `FastAPI.Depends` |
| [0003-uv-package-manager.md](06-adr/0003-uv-package-manager.md) | uv вместо poetry и pip |
| [0004-llm-fallback-resilience.md](06-adr/0004-llm-fallback-resilience.md) | Двухуровневая стратегия семантического поиска |
| [0005-infrastructure-packages.md](06-adr/0005-infrastructure-packages.md) | Раскладка `infrastructure/` по назначению, фасады пакетов |

## Кто владеет фактом

Один факт живёт ровно в одном документе, остальные на него ссылаются. Так
дубликаты не расходятся.

| Факт | Владелец |
| --- | --- |
| Значение термина | [Глоссарий](00-foundation/glossary.md) |
| Зачем существует система | [Видение продукта](00-foundation/product-vision.md) |
| Состав контейнеров и внешних систем | [Обзор и C4](01-architecture/overview.md) |
| Разрешённые направления импортов | [Слои и правила](01-architecture/layers-and-rules.md) |
| Состав домена: сущности, VO, политики, порты | [Модель предметной области](01-architecture/domain-model.md) |
| Порядок middleware и путь запроса | [Поток запроса](01-architecture/data-flow.md) |
| Скоупы и провайдеры Dishka | [DI на Dishka](01-architecture/di-dishka.md) |
| Таблицы, связи, ограничения | [Модель данных](01-architecture/data-model.md) |
| CSRF, заголовки, rate limiting | [Безопасность](01-architecture/security.md) |
| Публичность маршрута и `user_id` | [Матрица маршрутов](01-architecture/route-matrix.md) |
| Контракт конкретного провайдера | [Провайдеры источников](02-integrations-and-services/providers.md) |
| Цепочка LLM и деградация | [Умный поиск](02-integrations-and-services/llm-search.md) |
| Правила медиа-прокси | [Медиа-прокси](02-integrations-and-services/media-proxy.md) |
| Имя, тип и смысл переменной окружения | [Справочник переменных](03-ops/env-reference.md) |
| Порты, тома, режимы контейнера | [Развёртывание](03-ops/deployment.md) |
| Миграции, бэкапы, кэш | [Сопровождение](03-ops/maintenance.md) |
| Порядок добавления фичи | [Как добавить фичу](04-dev-guide/feature-workflow.md) |
| Стиль кода и коммитов | [Соглашения](04-dev-guide/conventions.md) |
| Уровень теста, нейминг, инструментарий | [Стратегия тестирования](05-testing/01-testing-strategy.md) |
| Канон unit-, integration- и e2e-теста | соответствующий документ в [05-testing](05-testing/) |
| Где объявляется фикстура и как изолировать состояние | [Фикстуры и изоляция](05-testing/05-fixtures-and-isolation.md) |
| Мотив архитектурного решения | соответствующая запись в [06-adr](06-adr/) |

## Генерируемые артефакты

Часть документов собирается из кода, поэтому не может разойтись с ним молча.

| Артефакт | Генератор | Гейт |
| --- | --- | --- |
| [api/openapi.json](api/openapi.json) — контракт JSON API | `uv run python scripts/export_openapi.py` | `uv run python scripts/export_openapi.py --check` (в CI и в `test_openapi_contract.py`) |
| [01-architecture/route-matrix.md](01-architecture/route-matrix.md) — механические колонки | `uv run python scripts/export_route_matrix.py` | ручное обновление по выводу скрипта |
| [01-architecture/importlinter-baseline.md](01-architecture/importlinter-baseline.md) — состав исключений | `uv run python scripts/export_importlinter_baseline.py` | `uv run python scripts/check_imports.py` |

`docs/api/openapi.json` — машинный файл: править его вручную нельзя, только
перегенерировать.

## Правила ведения документации

1. Язык документов — русский; код, имена переменных и команд — без перевода.
2. Термины берутся из [глоссария](00-foundation/glossary.md), сокращение проекта
   — **AEM**, а не «проект» и не «платформа».
3. Команды пишутся кроссплатформенно: `uv run ...` без привязки к shell конкретной
   ОС.
4. Диаграммы — только mermaid; таблицы выровнены и имеют заголовок.
5. Каждый документ строится по шаблону
   [templates/document-template.md](templates/document-template.md): описание,
   как работает, почему так, где в коде, связанные документы.
6. Незаполненных заглушек и списков «сделать позже» быть не должно: документ либо
   описывает действующее правило или поведение, либо его нет.
7. Ссылки между документами — относительные, чтобы работали и в IDE, и на GitHub.
8. Изменилось поведение — в том же изменении правится документ-владелец факта из
   таблицы выше.
