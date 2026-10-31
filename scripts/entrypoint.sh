#!/bin/sh
# Точка входа контейнера: режимы web (gunicorn) и dev (uvicorn --reload).
#
# Единственный источник схемы БД — Alembic. Если revision-файлов нет, контейнер
# останавливается с ошибкой вместо тихого создания таблиц через DATABASE_AUTO_INIT:
# в бою такой тихий путь оставил бы базу без истории версий.

set -e

cd /app

ALEMBIC_INI="migrations/alembic.ini"
VERSIONS_DIR="/app/migrations/versions"
MIGRATIONS_ATTEMPTS="${MIGRATIONS_ATTEMPTS:-5}"
MIGRATIONS_RETRY_DELAY="${MIGRATIONS_RETRY_DELAY:-3}"

apply_migrations() {
  if ! ls "$VERSIONS_DIR"/*.py >/dev/null 2>&1; then
    echo "ERROR: no revision files in $VERSIONS_DIR" >&2
    echo "ERROR: create one with: uv run alembic -c $ALEMBIC_INI revision --autogenerate -m \"initial schema\"" >&2
    exit 1
  fi

  attempt=1
  while [ "$attempt" -le "$MIGRATIONS_ATTEMPTS" ]; do
    if alembic -c "$ALEMBIC_INI" upgrade head; then
      return 0
    fi
    echo "WARN: alembic upgrade head failed (attempt $attempt/$MIGRATIONS_ATTEMPTS), retrying in ${MIGRATIONS_RETRY_DELAY}s" >&2
    attempt=$((attempt + 1))
    sleep "$MIGRATIONS_RETRY_DELAY"
  done

  echo "ERROR: alembic upgrade head did not succeed after $MIGRATIONS_ATTEMPTS attempts" >&2
  exit 1
}

apply_public_origin() {
  public_port="${APP_PUBLIC_PORT:-${APP_PORT:-5000}}"

  if [ -z "${APP_PUBLIC_HOST:-}" ]; then
    return 0
  fi

  public_origin="${APP_PUBLIC_SCHEME:-http}://${APP_PUBLIC_HOST}:${public_port}"

  case "${APP_BASE_URL:-}" in
    ""|"http://127.0.0.1:${public_port}"|"http://localhost:${public_port}")
      export APP_BASE_URL="$public_origin"
      ;;
  esac

  if [ -n "${APP_ALLOWED_ORIGINS:-}" ]; then
    case ",${APP_ALLOWED_ORIGINS}," in
      *",${public_origin},"*) ;;
      *) export APP_ALLOWED_ORIGINS="${APP_ALLOWED_ORIGINS},${public_origin}" ;;
    esac
  else
    export APP_ALLOWED_ORIGINS="http://localhost:${public_port},http://127.0.0.1:${public_port},${public_origin}"
  fi
}

if [ "$1" = "web" ]; then
  apply_public_origin

  if [ "${RUN_DB_MIGRATIONS:-1}" = "1" ]; then
    apply_migrations
  fi

  exec gunicorn \
    --bind "0.0.0.0:${APP_PORT:-5000}" \
    --worker-class "uvicorn.workers.UvicornWorker" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
    --access-logfile "-" \
    --error-logfile "-" \
    backend.main:app
fi

if [ "$1" = "dev" ]; then
  if [ "${RUN_DB_MIGRATIONS:-1}" = "1" ]; then
    apply_migrations
  fi

  exec uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "${APP_PORT:-5000}" \
    --reload \
    --reload-dir /app/src \
    --reload-dir /app/migrations \
    --reload-exclude '*.db' \
    --reload-exclude '__pycache__/*' \
    --reload-exclude '*.log'
fi

exec "$@"
