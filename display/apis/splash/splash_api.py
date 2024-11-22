from urllib.parse import quote

from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass


class SplashApi(ApiBaseClass):
    def __init__(
        self,
        baseurl: str,
        api_path: str = None,
        proxies: dict = None,
        user_agent: str = "Display",
        **kwargs,
    ):
        self.baseurl = baseurl
        self.api_path = api_path
        self.proxies = proxies
        self.user_agent = user_agent

        super().__init__(
            baseurl=self.baseurl,
            api_path=self.api_path,
            proxies=self.proxies,
            user_agent=self.user_agent,
            **kwargs,
        )

    def render_png(self, url, wait=5, timeout=30):
        resource = f"render.png?url={quote(url)}&timeout={timeout}&wait={wait}"

        return self.call("GET", resource=resource)

    def get_render_url(self, url, wait=5, timeout=30):
        resource = f"render.png?url={quote(url)}&timeout={timeout}&wait={wait}"

        return self._build_url(resource)
