#!/bin/sh
set -e

if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
  until nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
fi

python manage.py migrate --noinput
for app in accounts projects ohkr chat esb; do
  python manage.py migrate "$app" --noinput
done
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}"
