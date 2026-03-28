# Схема базы данных

## Описание

Приложение использует PostgreSQL как основное хранилище. В базе сохраняются пользователи и все продуктовые данные, которыми владеет сама система, а каталог аниме в основном остается внешним и подтягивается из Jikan, AniList и других провайдеров.

За миграции отвечает Alembic, активная конфигурация находится в `build/alembic/alembic.ini`.

## Как это работает

Основная схема данных:

```mermaid
erDiagram
    users ||--o{ highlights : creates
    users ||--o{ favorites : saves
    users ||--o{ user_anime_statuses : tracks
    users ||--o{ viewing_sessions : owns
    highlights ||--o{ highlight_contexts : enriches
    translations ||--o{ watch_sources : groups
    watch_sources ||--o{ viewing_sessions : resumes
    watch_sources ||--o{ highlight_contexts : anchors
    translations ||--o{ highlight_contexts : describes

    users {
        int id PK
        string email
        string username
        string password_hash
        string avatar_url
        datetime created_at
    }

    favorites {
        int id PK
        int user_id FK
        int anime_id
        string title
        string description
        string cover_url
        string genres_json
        datetime added_at
    }

    highlights {
        int id PK
        int user_id FK
        int anime_id
        int episode
        float start_timestamp
        float end_timestamp
        string description
        bool is_spoiler
        int likes_count
        string emotion
        datetime created_at
    }

    user_anime_statuses {
        int id PK
        int user_id FK
        int anime_id
        string status
        datetime updated_at
    }

    translations {
        int id PK
        int anime_id
        string name
        string translation_type
        string language
        datetime created_at
    }

    watch_sources {
        int id PK
        int anime_id
        int episode
        int translation_id FK
        string provider_name
        string source_name
        string stream_url
        string quality_label
        string source_type
        datetime created_at
    }

    viewing_sessions {
        int id PK
        int user_id FK
        int anime_id
        int episode
        int watch_source_id FK
        float position_seconds
        float volume
        string quality_label
        bool is_paused
        datetime updated_at
    }

    highlight_contexts {
        int id PK
        int highlight_id FK
        int watch_source_id FK
        int translation_id FK
        string title
        datetime created_at
    }
```

Ответственность таблиц:

- `users`: идентичность и профиль
- `favorites`: пользовательские закладки аниме с локальным snapshot-описанием карточки
- `highlights`: моменты из эпизодов, сохраненные пользователем
- `user_anime_statuses`: прогресс пользователя по тайтлам
- `translations`: логические варианты перевода или озвучки
- `watch_sources`: конкретные playable-источники от провайдеров
- `viewing_sessions`: состояние плеера для resume
- `highlight_contexts`: watch-контекст, привязанный к хайлайтам

Процесс миграций:

```powershell
alembic -c build/alembic/alembic.ini revision --autogenerate -m "описание изменения"
alembic -c build/alembic/alembic.ini upgrade head
```

## Почему это сделано так

- Схема хранит продуктовые данные, которые нельзя надежно держать только во внешних API.
- Избранное хранит локальный snapshot, потому что внешние идентификаторы и метаданные у разных провайдеров могут расходиться.
- Слой просмотра разложен на переводы, источники и сессии, чтобы плеер мог восстанавливать реальный контекст просмотра.
- Alembic делает эволюцию схемы явной и воспроизводимой в локальном запуске и в контейнерах.

## Где в коде

- `src/backend/infrastructure/models/sqlalchemy_models.py`
- `src/backend/infrastructure/files/database.py`
- `build/alembic/alembic.ini`
- `build/alembic/env.py`
- `build/alembic/versions`

## Связанные документы

- [Обзор архитектуры](../architecture/overview.md)
- [Деплой](../deployment/overview.md)
- [API и маршруты](../api/endpoints.md)
