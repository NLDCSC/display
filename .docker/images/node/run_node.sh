#!/bin/bash
set -e

cd /app && poetry run celery -A display.celery_app.display_daemon worker -Q nodes -P gevent -c 20 -O fair --loglevel=INFO \
--without-heartbeat --without-gossip --without-mingle
