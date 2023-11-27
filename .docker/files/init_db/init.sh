#!/bin/bash

FILE=INIT_COMPLETED

if [ -f "$FILE" ]; then
  echo "INIT Already performed, exiting!"
else
  echo "Starting DB INIT...."
  python3 -m db_migrate -u
  python3 -m scripts.setup_default_user
  python3 -m data.scripts.create_users
  touch "$FILE"
  echo "Done with DB INIT!!"
fi