#!/bin/bash
set -e

HOST="${HOST:-db}"
PORT="${PORT:-5432}"
USER="${USER:-postgres}"

echo "Waiting for PostgreSQL at $HOST:$PORT..."

while ! pg_isready -h "$HOST" -p "$PORT" -U "$USER" > /dev/null 2>&1; do
  echo "PostgreSQL is not ready yet, waiting..."
  sleep 2
done

echo "PostgreSQL is ready."

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "collectstatic failed, skipping"

echo "Starting Gunicorn..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000