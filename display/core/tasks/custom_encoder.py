import dataclasses
import json

from display.core.tasks.periodic_tasks import PeriodicTasks
from display.core.tasks.task_result import TaskResult

dataclass_mapping = {
    "__result_class__": TaskResult,
    "__periodic_class__": PeriodicTasks,
}


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            if isinstance(o, TaskResult):
                return {"__type__": "__result_class__", "data": dataclasses.asdict(o)}
            else:
                return dataclasses.asdict(o)
        elif isinstance(o, PeriodicTasks):
            data_dict = o.__dict__
            new_data_dict = {}

            for k, v in data_dict.items():
                new_data_dict[k.replace("_", "")] = v

            return {"__type__": "__periodic_class__", "data": new_data_dict}

        return super().default(o)


def custom_decoder(obj):
    if "__type__" in obj:
        return dataclass_mapping[obj["__type__"]](obj["data"])
    return obj


# Encoder function
def custom_dumps(obj):
    return json.dumps(obj, cls=CustomJSONEncoder)


# Decoder function
def custom_loads(obj):
    return json.loads(obj, object_hook=custom_decoder)
