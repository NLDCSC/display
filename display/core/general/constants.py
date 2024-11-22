from collections import namedtuple

TASK_START_MODULE = "display.celery_app.display_daemon"

user_active = namedtuple("user_active", "ENABLED DISABLED")(1, 2)

user_type = namedtuple("user_type", "NORMAL SYSTEM")(0, 1)

msg_cats = namedtuple("msg_cats", "OK NOK")("success", "error")

status_code = namedtuple("status_code", ["OK", "ERROR"])(0, 1)

user_permissions = namedtuple("user_permissions", "NONE READ WRITE")(0, 1, 2)

tracelog_result = namedtuple(
    "tracelog_result", "OK NOK UNK CHANGED NOT_CHANGED REQUESTED"
)("SUCCESS", "ERROR", "UNKNOWN", "CHANGED", "NOT_CHANGED", "REQUESTED")

tracelog_action = namedtuple(
    "tracelog_action",
    "SCREENSHOT EVIDENCE OD_SCREENSHOT STATE_CHANGE TIMELINE OD_EVIDENCE",
)("SCREENSHOT", "EVIDENCE", "OD SCREENSHOT", "STATE CHANGE", "TIMELINE", "OD EVIDENCE")

task_result = namedtuple("task_result", ["SUCCESS", "FAILURE"])(0, 1)

timeline_log_action = namedtuple(
    "timeline_log_action",
    [
        "NEW_USER",
        "PASSWORD_CHANGE",
        "USER_ACCOUNT_CHANGE",
        "USER_ACCOUNT_DELETED",
        "USER_ACCOUNT_ERROR",
        "GROUP_CHANGE",
        "LOGIN",
        "DAEMON_PING",
        "DAEMON_ACTION",
        "DATABASE_ACTIONS",
        "TASK_STARTED",
        "TASK_COMPLETED",
    ],
)(
    "NEW USER",
    "PASSWORD CHANGE",
    "USER ACCOUNT CHANGE",
    "USER ACCOUNT DELETED",
    "USER ACCOUNT ERROR",
    "GROUP CHANGE",
    "LOGIN",
    "DAEMON PING",
    "DAEMON ACTION",
    "DATABASE ACTIONS",
    "TASK STARTED",
    "TASK COMPLETED",
)
