#!/usr/bin/env bash
# Entrypoint for Dockerfile.render
set -euo pipefail

cd /srv/backend
python manage.py migrate --noinput

# Django API: internal only. 2 threads keep memory low (each tracking run starts a Chromium).
gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 1 \
  --threads 2 \
  --timeout 180 \
  --access-logfile - &

# Next.js: the only public process, listens on Render's $PORT.
cd /srv/frontend
HOSTNAME=0.0.0.0 node server.js &

# If either process exits, stop the container so Render restarts it.
wait -n
exit $?
