import dataclasses
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from display.core.general.data_class_validations import Validations
from display.core.general.utils import exclude_optional_dict
from display.webapp.app.models import Tracelog
from display.webapp.config import Config

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI, **{"pool_recycle": 299, "pool_timeout": 20}
)
Session = sessionmaker(engine)


@dataclass_json
@dataclass
class TraceLogEntry(Validations):
    url: str
    hash: str
    user: str
    action: str
    reason: str
    result: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    status_code: Optional[int | str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=1337
    )

    def save(self):
        with Session.begin() as session:
            try:
                timeline_entry = dataclasses.asdict(self)
                timeline_entry.pop("add_to_log", None)
                trace_log_entry = Tracelog(**timeline_entry, timestamp=int(time.time()))
                session.add(trace_log_entry)
            except Exception:
                raise
