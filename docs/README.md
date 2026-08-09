# Хаб документации

## Описание

Эта директория — навигационный слой проекта. Ее задача — сделать репозиторий читаемым как продукт: что делает система,
как она устроена, почему приняты конкретные решения и где каждая зона ответственности живет в коде.

## Как читать документацию

Начинать нужно с общей формы системы, затем перейти к домену, потом к интерфейсам и только после этого к
эксплуатационным аспектам:

1. [architecture/overview.md](architecture/overview.md)
2. [domain/core.md](domain/core.md)
3. [api/endpoints.md](api/endpoints.md)
4. [database/schema.md](database/schema.md)
5. [security/security.md](security/security.md)
6. [deployment/overview.md](deployment/overview.md)
7. [testing/strategy.md](testing/strategy.md)

Если нужен практический путь для нового разработчика, после архитектуры открывай [onboarding.md](onboarding.md).

## Карта документации

- Архитектура: [architecture/overview.md](architecture/overview.md)
- Доменная модель: [domain/core.md](domain/core.md)
- API и маршруты: [api/endpoints.md](api/endpoints.md)
- База данных и миграции: [database/schema.md](database/schema.md)
- Безопасность: [security/security.md](security/security.md)
- Деплой и runtime: [deployment/overview.md](deployment/overview.md)
- Тестовая стратегия: [testing/strategy.md](testing/strategy.md)
- Онбординг разработчика: [onboarding.md](onboarding.md)
- Конвенции: [conventions.md](conventions.md)
- Глоссарий: [glossary.md](glossary.md)
- Основные пользовательские сценарии: [use-cases.md](use-cases.md)
- Шаблон для новых документов: [templates/document-template.md](templates/document-template.md)

## Почему документация разбита именно так

- `architecture/` объясняет границы системы и поток запроса.
- `domain/` описывает продуктовые сущности и правила.
- `api/` описывает внешние и браузерные интерфейсы.
- `database/` описывает хранение данных и миграции.
- `security/` фиксирует текущую защищенность и пробелы.
- `deployment/` описывает запуск и упаковку системы.
- верхнеуровневые файлы нужны для работы людей с репозиторием.

## Где это в коде

- Точка входа: `../src/backend/main.py`
- Bootstrap backend: `src/backend/create_app.py`
- Frontend-шаблоны и статика: `src/frontend`
- Build-артефакты: `build`

## Связанные документы

- Вход в репозиторий: [../README.md](../README.md)
- Путь нового разработчика: [onboarding.md](onboarding.md)
- Правила разработки: [conventions.md](conventions.md)
