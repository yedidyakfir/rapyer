import abc
from abc import ABC

from redis.asyncio.client import Redis

from redis_pydantic.context import _context_var


class RedisType(ABC):
    def __init__(
        self,
        *args,
        redis_key: str = "",
        field_path: str = "",
        redis: Redis = None,
        **kwargs,
    ):
        self.redis_key = redis_key
        self.field_path = field_path
        self.redis = redis

    @property
    def pipeline(self):
        return _context_var.get() or self.redis

    @property
    def json_path(self):
        return f"$.{self.field_path}"

    @abc.abstractmethod
    def load(self):
        pass
