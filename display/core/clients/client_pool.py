from typing import List

from display.core.connections.client_connection import ClientConnection
from display.errors.display_errors import DisplayClientTypeError, DisplayClientMissing


class ClientPool(object):
    def __init__(self):
        self.pool = {}

    def add(self, client: ClientConnection):
        if not isinstance(client, ClientConnection):
            raise DisplayClientTypeError(
                "Provided argument is not of type ClientConnection, but of type {}".format(
                    type(client)
                )
            )

        self.pool[client.sid] = client

        return

    def remove(self, client_sid: str) -> ClientConnection:
        self.pool.pop(client_sid)
        return

    def get(self, client_sid: str) -> ClientConnection:
        try:
            return self.pool[client_sid]
        except KeyError:
            raise DisplayClientMissing

    def fetch_client_details(self) -> None:
        return {key: value.client_details() for (key, value) in self.pool.items()}

    def fetch_clients(self) -> List[ClientConnection]:
        return [client for client in self.pool.values()]

    def __repr__(self) -> str:
        return f"<< ClientPool >>"
