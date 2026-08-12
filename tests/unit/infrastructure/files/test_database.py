from __future__ import annotations

import pytest

from backend.infrastructure.files import database as database_module


class _FakeInspector:
    def __init__(self, table_names, columns):
        self._table_names = table_names
        self._columns = columns

    def get_table_names(self):
        return self._table_names

    def get_columns(self, table_name):
        return [{"name": item} for item in self._columns.get(table_name, [])]


class _FakeConnection:
    def __init__(self, statements):
        self.statements = statements

    def execute(self, statement):
        self.statements.append(str(statement))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeEngine:
    def __init__(self, statements):
        self.statements = statements

    def begin(self):
        return _FakeConnection(self.statements)


@pytest.mark.unit
class TestDatabaseBootstrap:
    """Юнит-тесты async-инициализации базы данных."""

    def test_create_db_engine_uses_driver_specific_options(self, monkeypatch):
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

        database_module.create_db_engine("sqlite:///test.db")
        database_module.create_db_engine("postgresql+asyncpg://user:pass@db:5432/app")

        assert calls == [
            ("sqlite:///test.db", {"echo": False, "connect_args": {"check_same_thread": False}}),
            ("postgresql+asyncpg://user:pass@db:5432/app", {"echo": False, "pool_pre_ping": True}),
        ]

    def test_create_session_factory_binds_engine(self, monkeypatch):
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

        database_module.create_session_factory("engine")

        assert captured["bind"] == "engine"

    def test_get_engine_creates_singleton_once(self, monkeypatch):
        """Что тестируем: get_engine лениво создает engine и переиспользует его.
        Что передаём: пустые глобалы и замоканный create_db_engine.
        Что ожидаем: engine создается один раз, повторные вызовы возвращают тот же объект.
        """
        calls = []
        monkeypatch.setattr(database_module, "engine", None)
        monkeypatch.setattr(
            database_module,
            "create_db_engine",
            lambda database_url: calls.append(database_url) or "engine",
        )

        first = database_module.get_engine()
        second = database_module.get_engine()

        assert first == "engine"
        assert second == "engine"
        assert calls == [database_module.Settings.database_url]

    def test_get_session_factory_creates_singleton_once(self, monkeypatch):
        """Что тестируем: get_session_factory лениво создает sessionmaker и переиспользует его.
        Что передаём: пустой глобал SessionLocal.
        Что ожидаем: factory создается один раз.
        """
        calls = []
        monkeypatch.setattr(database_module, "SessionLocal", None)
        monkeypatch.setattr(
            database_module,
            "create_session_factory",
            lambda engine: calls.append(engine) or object(),
        )
        monkeypatch.setattr(database_module, "get_engine", lambda: "engine")

        first = database_module.get_session_factory()
        second = database_module.get_session_factory()

        assert first == second
        assert calls == ["engine"]

    def test_ensure_watch_source_columns_adds_missing_source_type(self, monkeypatch):
        """Что тестируем: helper добавляет колонку source_type только когда ее не хватает.
        Что передаём: таблицу watch_sources без колонки source_type.
        Что ожидаем: выполняется ADD COLUMN для source_type.
        """
        statements = []
        fake_connection = _FakeConnection(statements)
        fake_inspector = _FakeInspector(
            ["watch_sources"],
            {"watch_sources": ["id", "anime_id", "episode"]},
        )
        monkeypatch.setattr(database_module, "inspect", lambda connection: fake_inspector)
        monkeypatch.setattr(database_module, "text", lambda sql: sql)

        database_module._ensure_watch_source_columns(fake_connection)

        assert statements == [
            "ALTER TABLE watch_sources ADD COLUMN source_type VARCHAR NOT NULL DEFAULT 'stream'"
        ]

    def test_ensure_favorite_columns_adds_all_missing_snapshot_columns(self, monkeypatch):
        """Что тестируем: helper добавляет недостающие snapshot-колонки favorites.
        Что передаём: таблицу favorites без snapshot-колонок.
        Что ожидаем: выполняются ADD COLUMN для всех недостающих колонок.
        """
        statements = []
        fake_connection = _FakeConnection(statements)
        fake_inspector = _FakeInspector(
            ["favorites"],
            {"favorites": ["id", "user_id", "anime_id"]},
        )
        monkeypatch.setattr(database_module, "inspect", lambda connection: fake_inspector)
        monkeypatch.setattr(database_module, "text", lambda sql: sql)

        database_module._ensure_favorite_columns(fake_connection)

        assert statements == [
            "ALTER TABLE favorites ADD COLUMN title VARCHAR",
            "ALTER TABLE favorites ADD COLUMN description VARCHAR",
            "ALTER TABLE favorites ADD COLUMN cover_url VARCHAR",
            "ALTER TABLE favorites ADD COLUMN genres_json VARCHAR",
        ]

    def test_ensure_highlight_columns_adds_all_missing_social_columns(self, monkeypatch):
        """Что тестируем: helper добавляет недостающие поля хайлайта для social-сценария.
        Что передаём: таблицу highlights без social-колонок.
        Что ожидаем: выполняются ADD COLUMN для всех недостающих колонок.
        """
        statements = []
        fake_connection = _FakeConnection(statements)
        fake_inspector = _FakeInspector(
            ["highlights"],
            {"highlights": ["id", "user_id", "anime_id", "episode"]},
        )
        monkeypatch.setattr(database_module, "inspect", lambda connection: fake_inspector)
        monkeypatch.setattr(database_module, "text", lambda sql: sql)

        database_module._ensure_highlight_columns(fake_connection)

        assert statements == [
            "ALTER TABLE highlights ADD COLUMN title VARCHAR NOT NULL DEFAULT ''",
            "ALTER TABLE highlights ADD COLUMN category VARCHAR",
            "ALTER TABLE highlights ADD COLUMN views_count INTEGER NOT NULL DEFAULT 0",
        ]

    async def test_get_session_yields_session_from_factory(self, monkeypatch):
        """Что тестируем: get_session отдает сессию с текущей session factory.
        Что передаём: session factory, возвращающую async-контекст-менеджер.
        Что ожидаем: get_session возвращает объект, созданный factory.
        """
        sentinel = object()

        class _FakeSession:
            async def __aenter__(self):
                return sentinel

            async def __aexit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr(database_module, "get_session_factory", lambda: lambda: _FakeSession())

        session = await anext(database_module.get_session())

        assert session is sentinel