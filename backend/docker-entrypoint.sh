#!/bin/sh
set -e

python apply_migrations.py

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
