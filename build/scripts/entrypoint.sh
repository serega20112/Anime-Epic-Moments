#!/bin/sh
set -e

cd /app

if [ "$1" = "web" ]; then
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
    --bind "0.0.0.0:${FLASK_PORT:-5000}" \
    --worker-class "uvicorn.workers.UvicornWorker" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    src.main:app
fi

exec "$@"
