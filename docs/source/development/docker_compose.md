# Docker-compose

If you would like to run this project in docker you should follow the following steps:

- clone the repo;
- add .env in root (copy from .env.example);
- add the necessary variables from display/webapp/config.py into the .env file (check the .env.example for inspiration)
- run `docker compose -f docker-compose_dev.yml watch`
- run `poetry install`
- run `poetry run python3 -m nldcsc.sql_migrations.flask_sql_migrate -u -a <<install_dir>>/app.py` to insert the
  database models into the database;
- run `poetry run python3 -m scripts.setup_default_user`;
- goto localhost:5050 (or whatever bind host and port you have configured in the docker compose file) and login as
  admin with provided password from the previous step.

Enjoy!
