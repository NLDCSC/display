import json
import time
from typing import Iterable

from nldcsc.flask_plugins.flask_redis import FlaskRedis
from redis import Redis


class AgeingList:
    def __init__(self, cache_prefix: str = "ageing_lists"):
        self._cache = FlaskRedis(init_standalone=True).redis_client
        self._KEY_PREFIX = f"{cache_prefix}:"

    @property
    def KEY_PREFIX(self) -> str:
        return self._KEY_PREFIX

    @property
    def cache(self) -> Redis:
        return self._cache

    def add(self, key: str, items: Iterable, ex: int = -1) -> None:
        if not items:
            return

        p = self._cache.pipeline()

        p.xadd(
            f"{self._KEY_PREFIX}{key}",
            {json.dumps(item): "" for item in items},
            f"{int(time.time())}-*",
        )

        if ex > 0:
            p.expire(key, ex)

        p.execute()

    def get(
        self, key: str, ex_at: int = None, delete: bool = False, approx: bool = True
    ):
        if ex_at is None:
            ex_at = "-"

        if delete:
            self.expire_items(key, ex_at, approx)

        if items := self._cache.xrange(f"{self._KEY_PREFIX}{key}", min=ex_at):
            return [json.loads(v) for _, item in items for v in item.keys()]
        return []

    def expire_items(self, key: str, ex_at: int, approx: bool = True):
        self._cache.xtrim(f"{self._KEY_PREFIX}{key}", minid=ex_at, approximate=approx)

    def get_expired(self, key: str, ex_from: int):
        if ex_from is None:
            ex_from = "+"

        if items := self._cache.xrange(f"{self._KEY_PREFIX}{key}", max=ex_from):
            return [json.loads(v) for _, item in items for v in item.keys()]
        return []
