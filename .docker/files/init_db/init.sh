#!/bin/bash

python3 -m db_migrate -u
python3 -m scripts.setup_default_user
python3 -m data.scripts.create_users