from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class TaskResult:
    status: int | str = None
    messages: dict[Any, Any] | List[dict[Any, Any]] = field(default_factory=list)
    errors: dict[Any, str] | List[dict[Any, str]] = field(default_factory=list)

    state: str | None = None
    cost: float = None
    inserted: int = None
    task_id: str = None

    def got_errors(self) -> bool:
        if isinstance(self.errors, dict):
            return True
        else:
            if len(self.errors) == 0:
                return False
            else:
                return True
