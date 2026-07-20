#!/bin/sh
set -eu

alembic -c services/api/alembic.ini upgrade head
PYTHONPATH=.:services/api python services/api/scripts/seed_commercial_catalogue.py
exec uvicorn app.main:app --app-dir services/api --host 0.0.0.0 --port "${PORT:-8000}"
