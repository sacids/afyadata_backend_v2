#!/bin/sh
set -e

if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
  until nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
fi

python manage.py makemigrations
python manage.py makemigrations accounts
python manage.py makemigrations projects
python manage.py makemigrations ohkr
python manage.py makemigrations chat
python manage.py makemigrations setup
python manage.py makemigrations esb
python manage.py migrate --noinput --skip-checks
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}"
