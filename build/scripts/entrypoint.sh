#!/bin/sh
set -e

cd /app

if [ "$1" = "web" ]; then
  public_port="${APP_PUBLIC_PORT:-${APP_PORT:-5000}}"
  public_origin=""

  if [ -n "${APP_PUBLIC_HOST:-}" ]; then
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
  fi

  if [ "${RUN_DB_MIGRATIONS:-1}" = "1" ]; then
    if ls /app/build/alembic/versions/*.py >/dev/null 2>&1; then
      alembic -c build/alembic/alembic.ini upgrade head
    else
      echo "Skipping Alembic migrations: no revision files found in /app/build/alembic/versions" >&2
      if [ "${DATABASE_AUTO_INIT:-0}" != "1" ]; then
        export DATABASE_AUTO_INIT=1
        echo "Enabled DATABASE_AUTO_INIT because Alembic revision files are missing" >&2
      fi
    fi
  elif [ "${DATABASE_AUTO_INIT:-0}" != "1" ]; then
    export DATABASE_AUTO_INIT=1
    echo "Enabled DATABASE_AUTO_INIT because RUN_DB_MIGRATIONS=0" >&2
  fi
  exec gunicorn \
    --bind "0.0.0.0:${APP_PORT:-5000}" \
    --worker-class "uvicorn.workers.UvicornWorker" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    backend.main:app
fi

exec "$@"
