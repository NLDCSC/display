from collections import namedtuple

msg_status = namedtuple("msg_status", "OK NOK")("success", "error")

tracelog_result = namedtuple(
    "tracelog_result", "OK NOK UNK CHANGED NOT_CHANGED REQUESTED"
)("SUCCESS", "ERROR", "UNKNOWN", "CHANGED", "NOT_CHANGED", "REQUESTED")

tracelog_action = namedtuple(
    "tracelog_action", "SCREENSHOT EVIDENCE OD_SCREENSHOT STATE_CHANGE"
)("SCREENSHOT", "EVIDENCE", "OD SCREENSHOT", "STATE CHANGE")
