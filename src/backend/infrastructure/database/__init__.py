"""Доступ к данным: сессии SQLAlchemy, единица работы, модели и репозитории.

Подпакет отвечает за всё, что связано с боевой базой PostgreSQL:

- :mod:`~backend.infrastructure.database.session` — движок, фабрика сессий, `Base`
  и проверка схемы при старте приложения;
- :mod:`~backend.infrastructure.database.unit_of_work` — граница транзакции,
  реализуемая портом `UnitOfWorkInterface` из application-слоя;
- :mod:`~backend.infrastructure.database.models` — ORM-модели по зонам данных;
- :mod:`~backend.infrastructure.database.repositories` — репозитории, возвращающие
  доменные сущности и не знающие про HTTP.

Схема базы описана миграциями Alembic в каталоге `migrations/` корня репозитория —
единственным источником структуры таблиц, как и для остальных окружений.
"""
