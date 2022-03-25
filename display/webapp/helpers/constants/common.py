from collections import namedtuple

msg_status = namedtuple("msg_status", "OK NOK")("success", "error")

trigram_version = namedtuple("trigram_version", "NORMAL REVERSE RANDOM_NAME RANDOM")(
    0, 1, 2, 3
)
