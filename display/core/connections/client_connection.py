from collections import namedtuple


class ClientConnection(object):
    connection_status = namedtuple(
        "connection_status", ("CON_REQ", "CON_ACK", "CON_CFM")
    )(1, 2, 3)

    def __init__(self, sid: str):
        self.sid = sid

        self.con_status = self.connection_status.CON_REQ

        self.current_tab = None

        self.current_tab_hash = None

    def client_details(self) -> dict:
        return {
            "sid": self.sid,
            "con_status": self.con_status,
            "current_tab": self.current_tab,
            "current_tab_hash": self.current_tab_hash,
        }

    def __repr__(self):
        return f"<< ClientConnection:{self.sid} >>"
