from json import dumps, loads

from nldcsc.flask_plugins.flask_redis import FlaskRedis
from redis_cache import RedisCache

from display.webapp.config import Config

config = Config()

redis_client = FlaskRedis(init_standalone=True).redis_client
cache = RedisCache(
    redis_client=redis_client,
    prefix="display_cache",
    serializer=dumps,
    deserializer=loads,
    key_serializer=None,
    support_cluster=True,
)
