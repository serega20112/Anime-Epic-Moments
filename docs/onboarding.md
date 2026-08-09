# Онбординг

## Описание

Этот документ — самый короткий практический путь для нового разработчика: как поднять приложение, понять структуру
репозитория и сделать первое безопасное изменение.

## Как это работает

### Чеклист первого часа

1. Прочитать [architecture/overview.md](architecture/overview.md).
2. Прочитать [domain/core.md](domain/core.md).
3. Создать `.env` на основе `.env.example`.
4. Установить Python-зависимости из `requirements.txt`.
5. Убедиться, что PostgreSQL доступен и `DATABASE_URL` указывает на него.
6. Применить миграции через Alembic.
7. Запустить приложение.
8. Прогнать backend-тесты.
9. Перед правками прочитать [conventions.md](conventions.md).

Команды:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
alembic -c build/alembic/alembic.ini upgrade head
python -m src.main
python -m pytest src/backend/tests -q
```

Куда смотреть для типовых задач:

- новый route или страница: `src/backend/delivery/api/v1` и `src/frontend/templates`
- новое бизнес-поведение: `src/backend/use_case`
- доменные правила: `src/backend/domain`
- изменение БД: `src/backend/infrastructure/models` и `build/alembic`
- новая внешняя интеграция: `src/backend/infrastructure/external`
- тесты: `src/backend/tests/backend`

## Почему это сделано так

- новый разработчик не должен разбирать репозиторий по импортам вслепую
- PostgreSQL и Alembic обязательны с первого дня, чтобы локальное поведение совпадало с runtime
- чтение архитектуры до начала правок снижает риск писать код не в том слое

## Где в коде

- `README.md`
- `../src/backend/main.py`
- `src/backend/create_app.py`
- `src/backend/dependencies/container.py`
- `build/docker-compose.yml`
- `build/alembic/alembic.ini`

## Связанные документы

- [Хаб документации](README.md)
- [Конвенции](conventions.md)
- [Тестовая стратегия](testing/strategy.md)
