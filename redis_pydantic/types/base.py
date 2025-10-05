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

    @abc.abstractmethod
    def clone(self):
        pass

    def serialize_value(self, value):
        return value

    def deserialize_value(self, value):
        return value


class GenericRedisType(RedisType, ABC):
    def __init__(self, inner_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inner_type = inner_type

    @classmethod
    def find_inner_type(cls, type_):
        if hasattr(type_, "__args__"):
            # For Dict types, we want the value type (second argument)
            # For List types, we want the element type (first argument)
            from typing import get_origin
            origin = get_origin(type_)
            if origin is dict and len(type_.__args__) >= 2:
                return cls.find_inner_type(type_.__args__[1])  # Value type for dict
            else:
                return cls.find_inner_type(type_.__args__[0])  # Element type for list
        return type_
