from collections import namedtuple

msg_status = namedtuple("msg_status", "OK NOK")("success", "error")

tracelog_result = namedtuple(
    "tracelog_result", "OK NOK UNK CHANGED NOT_CHANGED REQUESTED"
)(0, 1, 2, 3, 4, 5)

tracelog_result_dict = {
    0: "SUCCESS",
    1: "ERROR",
    2: "UNKNOWN",
    3: "CHANGED",
    4: "NOT_CHANGED",
    5: "REQUESTED",
}

tracelog_action = namedtuple(
    "tracelog_action", "SCREENSHOT EVIDENCE OD_SCREENSHOT STATE_CHANGE"
)(0, 1, 2, 3)

tracelog_action_dict = {
    0: "SCREENSHOT",
    1: "EVIDENCE",
    2: "OD SCREENSHOT",
    3: "STATE CHANGE",
}
