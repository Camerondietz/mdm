#!/usr/bin/env bash
# Container startup: wait for Postgres, migrate, collect static, then run the CMD.
set -e

echo "→ Waiting for the database to accept connections..."
python - <<'PYEOF'
import os, sys, time
import psycopg

conninfo = (
    f"host={os.environ.get('POSTGRES_HOST', 'db')} "
    f"port={os.environ.get('POSTGRES_PORT', '5432')} "
    f"dbname={os.environ.get('POSTGRES_DB', 'mdm')} "
    f"user={os.environ.get('POSTGRES_USER', 'mdm')} "
    f"password={os.environ.get('POSTGRES_PASSWORD', 'mdm')}"
)
for attempt in range(60):
    try:
        with psycopg.connect(conninfo, connect_timeout=3):
            print("  database is up.")
            break
    except Exception as exc:  # noqa: BLE001
        print(f"  not ready yet ({exc.__class__.__name__}); retrying in 2s...")
        time.sleep(2)
else:
    sys.exit("Database did not become available in time.")
PYEOF

echo "→ Applying database migrations..."
python manage.py migrate --noinput

echo "→ Collecting static files..."
python manage.py collectstatic --noinput

echo "→ Starting: $*"
exec "$@"
