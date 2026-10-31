"""Тесты инициализации и проверки схемы базы данных.

Отдельно проверяется, что стартовый путь больше не меняет структуру таблиц: `ALTER TABLE`
«для совместимости со старыми базами» был вторым источником схемы поверх Alembic и удалён,
а расхождение моделей и базы теперь останавливает запуск через :func:`verify_schema`.
"""

from __future__ import annotations

import pytest

import backend.infrastructure.database.models  # noqa: F401  — регистрирует таблицы в Base
from backend.infrastructure.database import session as database_module


class _FakeInspector:
    """Заменяет SQLAlchemy Inspector, отдавая заранее известную структуру базы."""

    def __init__(self, table_names, columns_by_table):
        """Сохранить видимые таблицы и их колонки.

        Args:
            table_names: Имена таблиц, которые «есть» в базе.
            columns_by_table: Словарь «таблица -> имена колонок».
        """
        self._table_names = table_names
        self._columns = columns_by_table

    def get_table_names(self):
        """Вернуть имена таблиц в базе.

        Returns:
            list[str]: Имена таблиц.
        """
        return self._table_names

    def get_columns(self, table_name):
        """Вернуть колонки таблицы в формате Inspector.

        Args:
            table_name: Имя таблицы.

        Returns:
            list[dict]: Колонки с ключом `name`.
        """
        return [{"name": item} for item in self._columns.get(table_name, [])]


class _RecordingConnection:
    """Фиксирует, какие синхронные операции были переданы в `run_sync`."""

    def __init__(self):
        """Инициализировать пустой журнал вызовов."""
        self.sync_calls: list[str] = []

    def run_sync(self, function):
        """Запомнить имя функции, не выполняя её на реальном соединении.

        Args:
            function: Синхронная callable, переданная из async-контекста.

        Returns:
            _Completed: Готовый awaitable результат.
        """
        self.sync_calls.append(getattr(function, "__name__", repr(function)))
        return _Completed()

    async def __aenter__(self):
        """Вернуть соединение как результат контекстного менеджера.

        Returns:
            _RecordingConnection: Само соединение.
        """
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Закрыть контекст без подавления исключений.

        Returns:
            bool: Всегда False.
        """
        return False


class _Completed:
    """Заглушка awaitable-результата `run_sync`."""

    def __await__(self):
        """Вернуть готовый результат без фактического выполнения.

        Yields:
            None: Немедленное завершение.

        Returns:
            None: Ничего.
        """
        return
        yield


class _FakeEngine:
    """Движок, чьё `begin()` возвращает записывающее соединение."""

    def __init__(self, connection):
        """Сохранить соединение для транзакции.

        Args:
            connection: Записывающее соединение.
        """
        self._connection = connection

    def begin(self):
        """Вернуть контекст транзакции.

        Returns:
            _RecordingConnection: Соединение-журнал.
        """
        return self._connection


def _metadata_table_names() -> list[str]:
    """Собрать имена всех таблиц моделей плюс служебная таблица Alembic.

    Returns:
        list[str]: Отсортированные имена таблиц.
    """
    return sorted([*database_module.Base.metadata.tables, "alembic_version"])


def _full_columns(table_name: str) -> list[str]:
    """Вернуть имена колонок таблицы по метаданным моделей.

    Args:
        table_name: Имя таблицы.

    Returns:
        list[str]: Имена колонок.
    """
    return [column.name for column in database_module.Base.metadata.tables[table_name].columns]


@pytest.mark.unit
class TestDatabaseBootstrap:
    """Юнит-тесты async-инициализации подключения к базе данных."""

    async def test_create_db_engine_uses_driver_specific_options(self, monkeypatch):
        """Что тестируем: create_db_engine выставляет connect_args для sqlite и pool_pre_ping для Postgres.
        Что передаём: два разных URL подключения.
        Что ожидаем: корректные kwargs для create_async_engine.
        """
        calls = []
        monkeypatch.setattr(
            database_module,
            "create_async_engine",
            lambda database_url, **kwargs: calls.append((database_url, kwargs)) or object(),
        )

        await database_module.create_db_engine("sqlite:///test.db")
        await database_module.create_db_engine("postgresql+asyncpg://user:pass@db:5432/app")

        assert calls == [
            ("sqlite:///test.db", {"echo": False, "connect_args": {"check_same_thread": False}}),
            ("postgresql+asyncpg://user:pass@db:5432/app", {"echo": False, "pool_pre_ping": True}),
        ]

    async def test_create_session_factory_binds_engine(self, monkeypatch):
        """Что тестируем: create_session_factory привязывает sessionmaker к engine.
        Что передаём: строку-заглушку engine.
        Что ожидаем: factory возвращает объект с привязкой к engine.
        """
        captured = {}
        monkeypatch.setattr(
            database_module,
            "async_sessionmaker",
            lambda **kwargs: captured.update(kwargs) or object(),
        )

        await database_module.create_session_factory("engine")

        assert captured["bind"] == "engine"

    async def test_get_engine_creates_singleton_once(self, monkeypatch):
        """Что тестируем: get_engine лениво создаёт engine и переиспользует его.
        Что передаём: пустые глобалы и замоканный create_db_engine.
        Что ожидаем: engine создаётся один раз, повторные вызовы возвращают тот же объект.
        """
        calls = []
        monkeypatch.setattr(database_module, "engine", None)

        async def _create_db_engine(database_url):
            calls.append(database_url)
            return "engine"

        monkeypatch.setattr(database_module, "create_db_engine", _create_db_engine)

        first = await database_module.get_engine()
        second = await database_module.get_engine()

        assert first == "engine"
        assert second == "engine"
        assert calls == [database_module.Settings.database_url]

    async def test_get_session_factory_creates_singleton_once(self, monkeypatch):
        """Что тестируем: get_session_factory лениво создаёт sessionmaker и переиспользует его.
        Что передаём: пустой глобал SessionLocal.
        Что ожидаем: factory создаётся один раз.
        """
        calls = []
        monkeypatch.setattr(database_module, "SessionLocal", None)

        async def _create_session_factory(engine):
            calls.append(engine)
            return object()

        async def _get_engine():
            return "engine"

        monkeypatch.setattr(database_module, "create_session_factory", _create_session_factory)
        monkeypatch.setattr(database_module, "get_engine", _get_engine)

        first = await database_module.get_session_factory()
        second = await database_module.get_session_factory()

        assert first == second
        assert calls == ["engine"]

    async def test_init_db_only_creates_tables_without_altering_schema(self, monkeypatch):
        """Регрессия: старт разработки не должен выполнять `ALTER TABLE`.

        Что тестируем: тело init_db.
        Что передаём: движок с записывающим соединением.
        Что ожидаем: в транзакцию передана единственная операция create_all — ни одного
        `_ensure_*_columns`, потому что структуру таблицы меняет только миграция Alembic.
        """
        connection = _RecordingConnection()
        engine = _FakeEngine(connection)
        monkeypatch.setattr(database_module, "engine", engine)

        await database_module.init_db()

        assert connection.sync_calls == ["create_all"]

    async def test_get_session_yields_session_from_factory(self, monkeypatch):
        """Что тестируем: get_session отдаёт сессию из текущей фабрики.
        Что передаём: фабрику, возвращающую async-контекст-менеджер.
        Что ожидаем: get_session возвращает созданный ею объект.
        """
        sentinel = object()

        class _FakeSession:
            async def __aenter__(self):
                return sentinel

            async def __aexit__(self, exc_type, exc, tb):
                return False

        async def _get_session_factory():
            return lambda: _FakeSession()

        monkeypatch.setattr(database_module, "get_session_factory", _get_session_factory)

        session = await anext(database_module.get_session())

        assert session is sentinel


@pytest.mark.unit
class TestSchemaVerification:
    """Юнит-тесты проверки соответствия схемы базы метаданным моделей."""

    def test_passes_when_database_matches_models(self, monkeypatch):
        """Что тестируем: _verify_schema_tables на совпадающей схеме.
        Что передаём: инспектор, повторяющий все таблицы и колонки моделей.
        Что ожидаем: исключения нет.
        """
        columns = {name: _full_columns(name) for name in database_module.Base.metadata.tables}
        monkeypatch.setattr(
            database_module,
            "inspect",
            lambda connection: _FakeInspector(_metadata_table_names(), columns),
        )

        database_module._verify_schema_tables(object())

    def test_raises_when_alembic_version_missing(self, monkeypatch):
        """Что тестируем: запуск против базы без истории версий.
        Что передаём: таблицы моделей без `alembic_version`.
        Что ожидаем: RuntimeError с подсказкой выполнить `alembic upgrade head`.
        """
        tables = sorted(database_module.Base.metadata.tables)
        columns = {name: _full_columns(name) for name in database_module.Base.metadata.tables}
        monkeypatch.setattr(
            database_module, "inspect", lambda connection: _FakeInspector(tables, columns)
        )

        with pytest.raises(RuntimeError, match="alembic_version"):
            database_module._verify_schema_tables(object())

    def test_raises_when_table_missing(self, monkeypatch):
        """Что тестируем: отсутствие таблицы, которую ждут модели.
        Что передаём: схему без таблицы `favorites`.
        Что ожидаем: RuntimeError перечисляет недостающие таблицы.
        """
        tables = [name for name in _metadata_table_names() if name != "favorites"]
        columns = {name: _full_columns(name) for name in tables if name != "alembic_version"}
        monkeypatch.setattr(
            database_module, "inspect", lambda connection: _FakeInspector(tables, columns)
        )

        with pytest.raises(RuntimeError, match="favorites"):
            database_module._verify_schema_tables(object())

    def test_raises_when_column_missing(self, monkeypatch):
        """Что тестируем: колонку, добавленную моделями, но не применённую миграцией.
        Что передаём: таблицу `users` без колонки `status`.
        Что ожидаем: RuntimeError указывает таблицу и колонку.
        """
        columns = {name: _full_columns(name) for name in database_module.Base.metadata.tables}
        columns["users"] = [name for name in columns["users"] if name != "status"]
        monkeypatch.setattr(
            database_module,
            "inspect",
            lambda connection: _FakeInspector(_metadata_table_names(), columns),
        )

        with pytest.raises(RuntimeError, match="users: status"):
            database_module._verify_schema_tables(object())

    def test_get_schema_drift_reports_both_levels(self, monkeypatch):
        """Что тестируем: get_schema_drift как чистую функцию сверки.
        Что передаём: схему без таблицы `highlights` и без колонки `cover_url` у коллекций.
        Что ожидаем: кортеж (список таблиц, словарь колонок) отражает оба расхождения.
        """
        columns = {name: _full_columns(name) for name in database_module.Base.metadata.tables}
        columns["anime_collections"] = [
            name for name in columns["anime_collections"] if name != "cover_url"
        ]
        tables = [name for name in _metadata_table_names() if name != "highlights"]
        columns.pop("highlights")
        monkeypatch.setattr(
            database_module, "inspect", lambda connection: _FakeInspector(tables, columns)
        )

        missing_tables, missing_columns = database_module.get_schema_drift(object())

        assert missing_tables == ["highlights"]
        assert missing_columns == {"anime_collections": ["cover_url"]}
