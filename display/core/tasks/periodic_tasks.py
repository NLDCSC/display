import json

from celery.schedules import crontab

from display.core.general.constants import TASK_START_MODULE


class PeriodicTasks(object):
    def __init__(self, schedule: int | dict, task: str, enabled: bool = True):
        self._schedule = schedule
        self._task = task
        self._enabled = enabled

    @property
    def dumps_schedule(self):
        return json.dumps(self._schedule)

    @property
    def schedule(self):
        if isinstance(self._schedule, int):
            return self._schedule
        else:
            try:
                return crontab(**self._schedule)
            except Exception:
                raise

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def task(self) -> str:
        return f"{TASK_START_MODULE}.{self._task}"

    def __eq__(self, other):
        if not isinstance(other, PeriodicTasks):
            return False
        return self._schedule == other._schedule and self._task == other._task

    def __hash__(self):
        return hash((self.dumps_schedule, self._task))

    def __repr__(self):
        return f"<<PeriodicTasks:{hash(self.schedule)}>>"
