from __future__ import annotations

from src.backend.infrastructure.files import database as database_module


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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        self.statements.append(str(statement))


class _FakeEngine:
    def __init__(self, statements):
        self.statements = statements

    def begin(self):
        return _FakeConnection(self.statements)


def test_get_session_returns_sessionlocal_result(monkeypatch):
    """Проверяем, что get_session возвращает объект, созданный текущим SessionLocal."""
    sentinel = object()
    monkeypatch.setattr(database_module, "SessionLocal", lambda: sentinel)

    assert database_module.get_session() is sentinel


def test_create_db_engine_uses_driver_specific_options(monkeypatch):
    """Проверяем, что create_db_engine выставляет connect_args для sqlite и pool_pre_ping для Postgres."""
    calls = []
    monkeypatch.setattr(
        database_module,
        "create_engine",
        lambda database_url, **kwargs: calls.append((database_url, kwargs)) or object(),
    )

    database_module.create_db_engine("sqlite:///test.db")
    database_module.create_db_engine("postgresql+psycopg://user:pass@db:5432/app")

    assert calls == [
        ("sqlite:///test.db", {"echo": False, "connect_args": {"check_same_thread": False}}),
        ("postgresql+psycopg://user:pass@db:5432/app", {"echo": False, "pool_pre_ping": True}),
    ]


def test_create_session_factory_binds_engine():
    """Проверяем, что create_session_factory создает sessionmaker, привязанный к переданному engine."""
    factory = database_module.create_session_factory("engine")

    assert factory.kw["bind"] == "engine"


def test_get_engine_creates_singleton_once(monkeypatch):
    """Проверяем, что get_engine лениво создает engine и затем переиспользует его."""
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


def test_init_db_creates_tables_and_runs_compatibility_steps(monkeypatch):
    """Проверяем, что init_db создает таблицы и запускает миграционные helper-функции."""
    calls = []
    fake_engine = object()
    monkeypatch.setattr(
        database_module.Base.metadata,
        "create_all",
        lambda bind: calls.append(("create_all", bind)),
    )
    monkeypatch.setattr(database_module, "get_engine", lambda: fake_engine)
    monkeypatch.setattr(
        database_module,
        "_ensure_watch_source_columns",
        lambda engine: calls.append(("watch", engine)),
    )
    monkeypatch.setattr(
        database_module,
        "_ensure_favorite_columns",
        lambda engine: calls.append(("favorite", engine)),
    )
    monkeypatch.setattr(
        database_module,
        "_ensure_highlight_columns",
        lambda engine: calls.append(("highlight", engine)),
    )

    database_module.init_db()

    assert calls[0] == ("create_all", fake_engine)
    assert ("watch", fake_engine) in calls
    assert ("favorite", fake_engine) in calls
    assert ("highlight", fake_engine) in calls


def test_ensure_watch_source_columns_adds_missing_source_type(monkeypatch):
    """Проверяем, что helper добавляет колонку source_type только когда ее не хватает."""
    statements = []
    fake_engine = _FakeEngine(statements)
    fake_inspector = _FakeInspector(
        ["watch_sources"],
        {"watch_sources": ["id", "anime_id", "episode"]},
    )
    monkeypatch.setattr(database_module, "engine", fake_engine)
    monkeypatch.setattr(database_module, "inspect", lambda engine: fake_inspector)

    database_module._ensure_watch_source_columns()

    assert statements == [
        "ALTER TABLE watch_sources ADD COLUMN source_type VARCHAR NOT NULL DEFAULT 'stream'"
    ]


def test_ensure_favorite_columns_adds_all_missing_snapshot_columns(monkeypatch):
    """Проверяем, что helper добавляет недостающие snapshot-колонки favorites."""
    statements = []
    fake_engine = _FakeEngine(statements)
    fake_inspector = _FakeInspector(
        ["favorites"],
        {"favorites": ["id", "user_id", "anime_id"]},
    )
    monkeypatch.setattr(database_module, "engine", fake_engine)
    monkeypatch.setattr(database_module, "inspect", lambda engine: fake_inspector)

    database_module._ensure_favorite_columns()

    assert statements == [
        "ALTER TABLE favorites ADD COLUMN title VARCHAR",
        "ALTER TABLE favorites ADD COLUMN description VARCHAR",
        "ALTER TABLE favorites ADD COLUMN cover_url VARCHAR",
        "ALTER TABLE favorites ADD COLUMN genres_json VARCHAR",
    ]


def test_ensure_highlight_columns_adds_all_missing_social_columns(monkeypatch):
    """Проверяем, что helper добавляет недостающие поля хайлайта для social-сценария."""
    statements = []
    fake_engine = _FakeEngine(statements)
    fake_inspector = _FakeInspector(
        ["highlights"],
        {"highlights": ["id", "user_id", "anime_id", "episode"]},
    )
    monkeypatch.setattr(database_module, "engine", fake_engine)
    monkeypatch.setattr(database_module, "inspect", lambda engine: fake_inspector)

    database_module._ensure_highlight_columns()

    assert statements == [
        "ALTER TABLE highlights ADD COLUMN title VARCHAR NOT NULL DEFAULT ''",
        "ALTER TABLE highlights ADD COLUMN category VARCHAR",
        "ALTER TABLE highlights ADD COLUMN views_count INTEGER NOT NULL DEFAULT 0",
    ]
