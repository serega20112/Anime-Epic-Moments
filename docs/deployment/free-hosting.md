# Бесплатный деплой (Render.com)

## Почему Render

- Бесплатный Web Service + PostgreSQL (90 дней, затем можно пересоздать или мигрировать на платный тир)
- Docker-деплой из коробки
- Redis не требуется: `KeyValueStore` автоматически использует in-memory fallback при `REDIS_REQUIRED=0`

## Подготовка

1. Убедитесь, что `build/Dockerfile` и `build/docker-compose.yml` в репозитории есть.
2. Убедитесь, что `requirements/base.txt` содержит продакшен-зависимости.
3. Запушьте проект на GitHub.

## Настройка PostgreSQL

1. Зайдите в [Render Dashboard](https://dashboard.render.com).
2. Создайте **New PostgreSQL**:
   - Name: `aem-db`
   - Database: `anime_epic_moments`
   - User: `anime_epic_moments`
   - Plan: **Free**
   - Region: выберите ближайший
3. После создания скопируйте **Internal Database URL** — он понадобится для переменных окружения.

## Настройка Web Service

1. В Render Dashboard → **New Web Service** → **Build and deploy from a Git repository**.
2. Выберите репозиторий.
3. Настройки:
   - **Name**: `anime-epic-moments`
   - **Runtime**: `Docker`
   - **Branch**: `main`
   - **Plan**: **Free**
4. В разделе **Environment Variables** добавьте:

```
SECRET_KEY=<сгенерируйте случайную строку>
DATABASE_URL=<Internal Database URL из шага выше>
DATABASE_AUTO_INIT=1
RUN_DB_MIGRATIONS=0
REDIS_ENABLED=0
REDIS_REQUIRED=0
COOKIE_SECURE=1
COOKIE_SAMESITE=Lax
APP_BASE_URL=https://anime-epic-moments.onrender.com
FLASK_DEBUG=0
MAX_REQUEST_BYTES=1048576
LOG_LEVEL=INFO
HSTS_MAX_AGE=63072000
ACCOUNT_LOCK_DURATION_SECONDS=1800
```

Параметры безопасности:
- `COOKIE_SECURE=1` включает HSTS-заголовок `Strict-Transport-Security: max-age=63072000; includeSubDomains` (значение из `HSTS_MAX_AGE`).
- `REDIS_REQUIRED=0` + `REDIS_ENABLED=0` переключают rate-limiter и account-lock на in-memory fallback.
- `ACCOUNT_LOCK_DURATION_SECONDS` управляет длительностью блокировки при brute-force.

5. Нажмите **Create Web Service**.

## После деплоя

Render автоматически:
- Соберёт Docker-образ на основе `build/Dockerfile`
- Установит зависимости из `requirements/base.txt`
- Запустит контейнер
- Применит `init_db()` (благодаря `DATABASE_AUTO_INIT=1`)

Первый запуск может занять 2-5 минут на Free плане (cold start).

## Redis и fallback

При `REDIS_ENABLED=0` или недоступном Redis-сервере система автоматически переключается на in-memory хранилище:
- `KeyValueStore` использует thread-safe in-memory dict с TTL.
- Rate limiter и account lock работают без Redis.
- Ограничение: данные блокировок хранятся в памяти одного инстанса и сбрасываются при рестарте.

## Ограничения Free плана

- **PostgreSQL**: база живёт 90 дней, затем нужно пересоздать. Сохраните дамп перед истечением:
  ```
  # через Render CLI или pg_dump
  ```
- **Web Service**: засыпает после 15 минут бездействия. Просыпается при первом запросе (15-30 сек).
- **Хранилище**: ephemeral (любые записанные файлы исчезают при перезапуске). Для хранения файлов (аватары, изображения) используйте внешнее S3-совместимое хранилище (например, Backblaze B2 бесплатно до 10GB).

## Альтернативы

- **Fly.io**: $5 кредитов в месяц на аккаунт, хватает на одну micro-VM. Требует `fly.toml` конфигурацию.
- **Railway**: триальный период с кредитами, потом от $5/мес.
- **Koyeb**: бесплатный тир с Docker-деплоем, без спячки, но один сервис.