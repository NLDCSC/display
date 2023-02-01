#/bin/bash
cd ..

export DEBUG=True

export LOG_FILE_PATH=/home/paul/PycharmProjects/display/dev_data/flask/logs

export CONFIG_PATH=/home/paul/PycharmProjects/display/dev_data/flask/config

export SCREENSHOT_LOCATION=/home/paul/PycharmProjects/display/dev_data/flask/screenshots

export TIMELINE_LOCATION=/home/paul/PycharmProjects/display/dev_data/flask/timeline

export REDIS_URL=redis://localhost:6379/

export SPLASH_HOST=localhost

export LOG_LEVEL=DEBUG

celery -A display.celery_app.display_daemon worker --loglevel=INFO -B -O fair --without-heartbeat --without-gossip --without-mingle
