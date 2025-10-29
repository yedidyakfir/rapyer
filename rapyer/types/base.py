import abc
import base64
import pickle
from abc import ABC
from typing import get_args, Any, TypeVar, Generic, get_origin

from pydantic import GetCoreSchemaHandler, TypeAdapter, BaseModel
from pydantic_core import core_schema
from pydantic_core.core_schema import ValidationInfo, CoreSchema, SerializationInfo

from rapyer.config import RedisFieldConfig, RedisConfig
from rapyer.context import _context_var
from rapyer.utils import safe_issubclass

REDIS_DUMP_FLAG_NAME = "__rapyer_dumped__"


class RedisType(ABC):
    original_type: type = None
    field_path: str = None
    _adapter: TypeAdapter = None

    @property
    def redis(self):
        return self._base_model_link.Meta.redis

    @property
    def redis_key(self):
        return self._base_model_link.key

    @property
    def Meta(self):
        return self._base_model_link.Meta

    def __init__(self, *args, **kwargs):
        # Note: This should be overridden in the base class AtomicRedisModel, it would allow me to get access to a redis key
        self._base_model_link = None

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls, handler(cls.original_type)
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

    def sub_field_path(self, field_name: str):
        return f"{self.field_path}.{field_name}"

    def json_field_path(self, field_name: str):
        return f"$.{self.sub_field_path(field_name)}"

    @abc.abstractmethod
    async def load(self):
        pass

    @abc.abstractmethod
    def clone(self):
        pass

    @staticmethod
    def serialize_unknown(value: Any):
        return base64.b64encode(pickle.dumps(value)).decode("utf-8")

    @staticmethod
    def deserialize_unknown(value: str):
        return pickle.loads(base64.b64decode(value))


T = TypeVar("T")


class GenericRedisType(RedisType, Generic[T], ABC):
    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[0] if args else Any

    def create_new_type(self, key):
        inner_original_type = self.find_inner_type(self.original_type)
        type_transformer = RedisTypeTransformer(
            self.sub_field_path(key), self.Meta, self._base_model_link._base_redis_type
        )
        inner_type_orig = get_origin(inner_original_type) or inner_original_type
        inner_type_args = get_args(inner_original_type)
        new_type = type_transformer[inner_type_orig, inner_type_args]
        return new_type

    def create_new_value_with_adapter(self, key, value):
        new_type = self.create_new_type(key)
        if new_type is Any:
            return value, TypeAdapter(Any)
        if issubclass(new_type, BaseModel):
            adapter = TypeAdapter(new_type)
        elif issubclass(new_type, RedisType):
            adapter = new_type._adapter  # noqa
        else:
            return value, TypeAdapter(new_type)
        normalized_object = adapter.validate_python(
            value, context={REDIS_DUMP_FLAG_NAME: True}
        )
        return normalized_object, adapter

    def create_new_value(self, key, value):
        new_value, adapter = self.create_new_value_with_adapter(key, value)
        return new_value

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
    def __init__(
        self, field_name: str, redis_config: RedisConfig, pydantic_base_redis: type
    ):
        self.field_name = field_name
        self.redis_config = redis_config
        self.pydantic_base_redis = pydantic_base_redis

    def __getitem__(self, item: type):
        if isinstance(item, tuple):
            origin, args = item
        else:
            origin, args = item, None
        if origin is Any:
            return item

        if safe_issubclass(origin, self.pydantic_base_redis):
            field_conf = RedisFieldConfig(field_path=self.field_name)
            return type(
                origin.__name__,
                (origin,),
                dict(field_config=field_conf),
            )
        if safe_issubclass(origin, BaseModel):
            origin: type[BaseModel]
            field_conf = RedisFieldConfig(field_path=self.field_name)
            return type(
                f"Redis{origin.__name__}",
                (origin, self.pydantic_base_redis),
                dict(field_config=field_conf),
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
            dict(field_path=self.field_name, original_type=original_type),
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
