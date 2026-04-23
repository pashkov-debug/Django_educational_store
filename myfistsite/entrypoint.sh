#!/usr/bin/env sh
set -eu

mkdir -p /app/media

if [ ! -f /app/db.sqlite3 ]; then
  echo "SQLite database not found. It will be created by migrations."
fi

python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000
