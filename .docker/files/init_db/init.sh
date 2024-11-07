#!/bin/bash

FILE=/app/data/INIT_COMPLETED

if [ -f "$FILE" ]; then
  echo "INIT Already performed, checking for upgrade!"
  poetry run python3 -m flask db upgrade
  echo "Done with DB UPGRADE!"
else
  echo "Starting DB INIT...."
  poetry run python3 -m flask db upgrade
  poetry run python3 -m scripts.setup_default_user
  touch "$FILE"
  echo "Done with DB INIT!!"
fi