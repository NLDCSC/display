from collections import namedtuple

user_active = namedtuple("user_active", "ENABLED DISABLED")(1, 2)

user_type = namedtuple("user_type", "NORMAL SYSTEM")(0, 1)

msg_cats = namedtuple("msg_cats", "OK NOK")("success", "error")

user_permissions = namedtuple("user_permissions", "NONE READ WRITE")(0, 1, 2)

tracelog_result = namedtuple(
    "tracelog_result", "OK NOK UNK CHANGED NOT_CHANGED REQUESTED"
)("SUCCESS", "ERROR", "UNKNOWN", "CHANGED", "NOT_CHANGED", "REQUESTED")

tracelog_action = namedtuple(
    "tracelog_action", "SCREENSHOT EVIDENCE OD_SCREENSHOT STATE_CHANGE TIMELINE"
)("SCREENSHOT", "EVIDENCE", "OD SCREENSHOT", "STATE CHANGE", "TIMELINE")
