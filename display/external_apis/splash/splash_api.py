"""
splash_api.py
=============
"""
from urllib.parse import quote

from display.external_apis.generic_api import GenericApi


class SplashApi(GenericApi):
    def __init__(
        self,
        address,
        api_path=None,
        proxies=None,
        protocol="https",
        user_agent="Display",
    ):
        self.address = address
        self.api_path = api_path
        self.proxies = proxies
        self.protocol = protocol
        self.user_agent = user_agent

        super().__init__(
            self.address, self.api_path, self.proxies, self.protocol, self.user_agent
        )

    def render_png(self, url, wait=5, timeout=30):
        resource = f"render.png?url={quote(url)}&timeout={timeout}&wait={wait}"

        return self.call("GET", resource=resource)

    def get_render_url(self, url, wait=5, timeout=30):
        resource = f"render.png?url={quote(url)}&timeout={timeout}&wait={wait}"

        return self._build_url(resource)
