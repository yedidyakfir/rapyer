import abc
from abc import ABC
from typing import get_args, Callable, Any

from redis.asyncio.client import Redis

from rapyer.context import _context_var


class RedisSerializer(ABC):
    def __init__(self, full_type: type, serializer_creator: Callable):
        self.full_type = full_type
        self.serializer_creator = serializer_creator

    def serialize_value(self, value):
        return value

    def deserialize_value(self, value):
        return value


class PydanicSerializer(RedisSerializer):
    def serialize_value(self, value):
        if isinstance(value, dict):
            return value
        return value.model_dump()

    def deserialize_value(self, value):
        return self.full_type(**value)


class RedisType(ABC):
    serializer: RedisSerializer = None

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
        return self.serializer.serialize_value(value)

    def deserialize_value(self, value):
        return self.serializer.deserialize_value(value)


class GenericRedisType(RedisType, ABC):
    def __init__(
        self,
        serializer_creator: Callable,
        type_creator: Callable,
        inst_init: Callable,
        full_type: type,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.serializer_creator = serializer_creator
        self.type_creator = type_creator
        self.inst_init = inst_init
        self.full_type = full_type
        inner_type = self.find_inner_type(full_type)
        self.serializer = serializer_creator(inner_type)
        self.inner_type = self.type_creator("lst", inner_type)

    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[0] if args else Any
