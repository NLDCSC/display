from dotenv import load_dotenv

load_dotenv("./.env")

from display.webapp.run import create_app
from set_version import VERSION

import argparse
import os
from subprocess import run, PIPE, STDOUT

argparser = argparse.ArgumentParser(
    description="migrate/update the orbit database schema"
)

argparser.add_argument("-i", action="store_true", help="Setup new migration directory")
argparser.add_argument("-m", action="store_true", help="Migrate the database")
argparser.add_argument("-u", action="store_true", help="Update the database")
args = argparser.parse_args()

current_dir = os.path.dirname(os.path.realpath(__file__))

__version__ = VERSION


def create_app():

    app, socketio = create_app(version=__version__)

    return app


if __name__ == "__main__":

    init = "flask db init"

    migrate = "flask db migrate"

    update = "flask db upgrade"

    if args.i:
        result = run(
            init,  # nosec
            stdout=PIPE,
            stderr=STDOUT,
            universal_newlines=True,
            shell=True,
            cwd=current_dir,
        )

        print(
            {
                "code": result.returncode,
                "stdout": str(result.stdout)
                .replace("\x1b[37m", "")
                .replace("\x1b[0m\n", ""),
            }
        )

    if args.m:
        result = run(
            migrate,  # nosec
            stdout=PIPE,
            stderr=STDOUT,
            universal_newlines=True,
            shell=True,
            cwd=current_dir,
        )

        print(
            {
                "code": result.returncode,
                "stdout": str(result.stdout)
                .replace("\x1b[37m", "")
                .replace("\x1b[0m\n", ""),
            }
        )

    if args.u:
        result = run(
            update,  # nosec
            stdout=PIPE,
            stderr=STDOUT,
            universal_newlines=True,
            shell=True,
            cwd=current_dir,
        )

        print(
            {
                "code": result.returncode,
                "stdout": str(result.stdout)
                .replace("\x1b[37m", "")
                .replace("\x1b[0m\n", ""),
            }
        )
