from display.helpers.errors import DisplayClientTypeError
from display.objects.client_connection import ClientConnection


class ClientPool(object):
    def __init__(self):

        self.pool = {}

    def add(self, client):

        if not isinstance(client, ClientConnection):
            raise DisplayClientTypeError(
                "Provided argument is not of type ClientConnection, but of type {}".format(
                    type(client)
                )
            )

        self.pool[client.sid] = client

        return

    def remove(self, client_sid):

        self.pool.pop(client_sid)
        return

    def get(self, client_sid):

        return self.pool[client_sid]

    def fetch_client_details(self):

        return {key: value.client_details() for (key, value) in self.pool.items()}

    def fetch_clients(self):

        return [client for client in self.pool.values()]

    def __repr__(self):
        return f"<< ClientPool >>"
