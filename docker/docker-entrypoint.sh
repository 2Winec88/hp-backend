#!/bin/sh
set -e

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

python - <<'PY'
import os
import socket
import time

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))

for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("PostgreSQL did not become available in time.")
PY

python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000
