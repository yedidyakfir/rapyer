import abc
from abc import ABC
from typing import get_args

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
        return _context_var.get()

    @property
    def client(self):
        return _context_var.get() or self.redis

    @property
    def json_path(self):
        return f"$.{self.field_path}"

    def json_field_path(self, field_name: str):
        return f"{self.json_path}.{field_name}"

    @abc.abstractmethod
    async def load(self):
        pass

    @abc.abstractmethod
    def clone(self):
        pass

    def serialize_value(self, value):
        return value

    def deserialize_value(self, value):
        return value


class GenericRedisType(RedisType, ABC):
    def __init__(self, inner_type: RedisType, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inner_type = inner_type

    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[0]
