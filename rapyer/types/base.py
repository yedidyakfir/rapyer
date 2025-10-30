import abc
import base64
import pickle
from abc import ABC
from typing import get_args, Any, TypeVar, Generic, Self

from pydantic import GetCoreSchemaHandler, TypeAdapter, BaseModel, PrivateAttr
from pydantic_core import core_schema
from pydantic_core.core_schema import ValidationInfo, CoreSchema, SerializationInfo

from rapyer.config import RedisConfig
from rapyer.context import _context_var
from rapyer.utils import safe_issubclass

REDIS_DUMP_FLAG_NAME = "__rapyer_dumped__"


class RedisType(ABC):
    original_type: type = None
    field_name: str = None
    _adapter: TypeAdapter = None

    @property
    def redis(self):
        return self._base_model_link.Meta.redis

    @property
    def key(self):
        return self._base_model_link.key

    @property
    def Meta(self):
        return self._base_model_link.Meta

    @property
    def field_path(self) -> str:
        base_path = self._base_model_link.field_path
        # TODO - This method is terrible, need to think on other way
        seperator = "" if self.field_name.startswith("[") else "."
        return (
            f"{base_path}{seperator}{self.field_name}" if base_path else self.field_name
        )

    @property
    def pipeline(self):
        return _context_var.get()

    @property
    def client(self):
        return _context_var.get() or self.redis

    @property
    def json_path(self):
        return f"$.{self.field_path}"

    def __init__(self, *args, **kwargs):
        # Note: This should be overridden in the base class AtomicRedisModel, it would allow me to get access to a redis key
        self._base_model_link = None

    def init_redis_field(self, key, val):
        if hasattr(val, "_base_model_link"):
            val._base_model_link = self
            val.field_name = key

    def sub_field_path(self, field_name: str):
        return f"{self.field_path}.{field_name}"

    def json_field_path(self, field_name: str):
        return f"$.{self.sub_field_path(field_name)}"

    async def save(self) -> Self:
        model_dump = self._adapter.dump_python(
            self, mode="json", context={REDIS_DUMP_FLAG_NAME: True}
        )
        await self.client.json().set(self.key, self.json_path, model_dump)
        if self.Meta.ttl is not None:
            await self.client.expire(self.key, self.Meta.ttl)
        return self

    @abc.abstractmethod
    async def load(self):
        pass

    @abc.abstractmethod
    def clone(self):
        pass

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls, handler(cls.original_type)
        )

    @staticmethod
    def serialize_unknown(value: Any):
        return base64.b64encode(pickle.dumps(value)).decode("utf-8")

    @staticmethod
    def deserialize_unknown(value: str):
        return pickle.loads(base64.b64decode(value))


T = TypeVar("T")


class GenericRedisType(RedisType, Generic[T], ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, val in self.iterate_items():
            self.init_redis_field(key, val)

    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[0] if args else Any

    @abc.abstractmethod
    def iterate_items(self):
        pass

    @classmethod
    @abc.abstractmethod
    def full_serializer(cls, value, info: SerializationInfo):
        pass

    @classmethod
    @abc.abstractmethod
    def full_deserializer(cls, value, info: ValidationInfo):
        pass

    @classmethod
    @abc.abstractmethod
    def schema_for_unknown(cls):
        pass

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        # Extract the generic type argument T from source_type
        element_type = cls.find_inner_type(source_type)

        if element_type is Any:
            # Build schema with both validator and serializer
            python_schema = core_schema.with_info_before_validator_function(
                cls.full_deserializer, handler(cls.original_type)
            )

            return core_schema.with_info_after_validator_function(
                lambda v, info: cls(v),
                python_schema,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    cls.full_serializer,
                    info_arg=True,
                    return_schema=cls.schema_for_unknown(),
                ),
            )
        else:
            # Normal serialization for concrete types
            return core_schema.no_info_after_validator_function(
                cls, handler(cls.original_type)
            )


class RedisTypeTransformer:
    def __init__(self, field_name: str, redis_config: RedisConfig):
        self.field_name = field_name
        self.redis_config = redis_config

    def __getitem__(self, item: type):
        if isinstance(item, tuple):
            origin, args = item
        else:
            origin, args = item, None
        if origin is Any:
            return origin

        from rapyer.base import AtomicRedisModel

        if safe_issubclass(origin, AtomicRedisModel):
            return type(
                origin.__name__,
                (origin,),
                dict(_field_name=PrivateAttr(default=self.field_name)),
            )
        if safe_issubclass(origin, BaseModel):
            origin: type[BaseModel]
            # TODO - check if switch order inheritance change something
            return type(
                f"Redis{origin.__name__}",
                (AtomicRedisModel, origin),
                dict(_field_name=PrivateAttr(default=self.field_name)),
            )

        if safe_issubclass(origin, RedisType):
            redis_type = origin
            original_type = origin.original_type
        else:
            redis_type = self.redis_config.redis_type[origin]
            original_type = origin
            if args:
                original_type = original_type[args]

        new_type = type(
            redis_type.__name__,
            (redis_type,),
            dict(field_name=self.field_name, original_type=original_type),
        )

        if issubclass(redis_type, RedisType):
            adapter_type = new_type
            try:
                adapter_type = adapter_type[args]
            except TypeError:
                pass
            new_type._adapter = TypeAdapter(adapter_type)
        return new_type

    def __contains__(self, item: type):
        if safe_issubclass(item, BaseModel):
            return True
        if safe_issubclass(item, RedisType):
            return True
        return item in self.redis_config.redis_type
