import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from display.errors.trace_log_errors import ValidationError
from display.webapp.app.models import tracelog
from display.webapp.config import Config

config = Config()

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, **{"pool_recycle": 299, "pool_timeout": 20})
Session = sessionmaker(engine)


class TraceLog(object):
    """
    The TraceLog class is the class that handles the logging of all actions and results into the backend database.
    """

    @staticmethod
    def insert(entry: dict):

        with Session.begin() as session:
            try:
                if TraceLog.validate(entry=entry):
                    new_entry = tracelog(**entry, timestamp=int(time.time()))
                    session.add(new_entry)
            except ValidationError:
                raise

    @staticmethod
    def multiple_insert(entries: list[dict]):

        with Session.begin() as session:
            for entry in entries:
                try:
                    if TraceLog.validate(entry=entry):
                        new_entry = tracelog(**entry, timestamp=int(time.time()))

                        session.add(new_entry)
                except ValidationError:
                    pass

    @staticmethod
    def validate(entry: dict):

        excluded_entries = ["id", "registry", "metadata", "timestamp"]

        key_list = [
            x
            for x in tracelog().__dir__()
            if not x.startswith("_")
            and not x.startswith("query")
            and x not in excluded_entries
        ]

        # just checking if the entry has keys that are in the key_list; return False if not else return True
        entry_keys = list(entry.keys())

        test_result = [(x in key_list) for x in entry_keys]

        if not all(test_result):
            raise ValidationError(
                f"The supplied data: {entry}, has keys that are not part of the tracelog data model and "
                f"therefore failed validation"
            )

        return all(test_result)

    def __repr__(self):
        return f"<< TraceLog >>"
