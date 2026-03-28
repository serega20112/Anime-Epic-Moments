#!/bin/sh
set -e

cd /app

if [ "$1" = "web" ]; then
  if [ "${RUN_DB_MIGRATIONS:-1}" = "1" ]; then
    alembic -c build/alembic/alembic.ini upgrade head
  fi
  exec gunicorn \
    --bind "0.0.0.0:${FLASK_PORT:-5000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    src.main:app
fi

exec "$@"
