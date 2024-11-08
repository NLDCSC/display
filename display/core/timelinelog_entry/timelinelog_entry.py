import dataclasses
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from certexmon.core.general.constants import timeline_log_action
from certexmon.core.general.data_class_validations import Validations
from certexmon.core.general.utils import exclude_optional_dict
from certexmon.webapp.app.definitions.core import Logs, Timeline
from certexmon.webapp.config import Config
from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI, **{"pool_recycle": 299, "pool_timeout": 20}
)
Session = sessionmaker(engine)


timeline_action_list = [
    timeline_log_action.SOCKET_CREATED,
    timeline_log_action.SOCKET_MODIFIED,
    timeline_log_action.SOCKET_DELETED,
    timeline_log_action.SOCKET_CLOSED,
    timeline_log_action.DOMAIN_CREATED,
    timeline_log_action.DOMAIN_MODIFIED,
    timeline_log_action.DOMAIN_DELETED,
    timeline_log_action.SCANRANGE_CREATED,
    timeline_log_action.SCANRANGE_MODIFIED,
    timeline_log_action.SCANRANGE_DELETED,
    timeline_log_action.SCANNED,
    timeline_log_action.STATUS_CHANGE,
]


@dataclass_json
@dataclass
class TimeLineLogEntry(Validations):
    user: str
    action: str
    ip_addr: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    message: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    result: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    add_to_timeline: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=False
    )
    add_to_log: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=True
    )
    socket_parent: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=0
    )
    domain_parent: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=0
    )
    subdomain_parent: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=0
    )
    scope_parent: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=0
    )
    task_type: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=1337
    )
    task_file: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    task_id: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    custom_task: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=0
    )

    def validate_action(self, value, **_) -> str:
        if self.add_to_timeline and value not in timeline_action_list:
            raise ValueError("Invalid action value for timeline entry.")
        return value

    def save(self):
        with Session.begin() as session:
            try:
                timeline_entry = dataclasses.asdict(self)
                timeline_entry.pop("add_to_timeline")
                timeline_entry.pop("add_to_log")
                log_entry = timeline_entry.copy()

                if log_entry.get("result", None) is None:
                    log_entry["result"] = log_entry.pop("message")
                else:
                    log_entry.pop("message")

                log_entry.pop("socket_parent")
                log_entry.pop("domain_parent")
                log_entry.pop("scope_parent")
                log_entry.pop("subdomain_parent")
                log_entry.pop("task_type")
                log_entry.pop("task_file")
                log_entry.pop("task_id")
                log_entry.pop("custom_task")
                if self.add_to_timeline:
                    timeline_entry.pop("ip_addr")
                    new_timeline_entry = Timeline(
                        **timeline_entry, created=int(time.time())
                    )
                    if self.add_to_log:
                        session.add(Logs(**log_entry, created=int(time.time())))
                    session.add(new_timeline_entry)
                else:
                    if self.add_to_log:
                        new_log_entry = Logs(**log_entry, created=int(time.time()))
                        session.add(new_log_entry)
            except Exception:
                raise
