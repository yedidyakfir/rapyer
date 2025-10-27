import abc
import base64
import pickle
from abc import ABC
from typing import get_args, Any

from pydantic import GetCoreSchemaHandler, TypeAdapter, BaseModel
from pydantic_core import core_schema

from rapyer.context import _context_var
from rapyer.utils import RedisTypeTransformer


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


class BaseRedisType(ABC):
    field_path: str = ""


class RedisType(BaseRedisType):
    original_type: type = None
    full_type: type = None
    field_path: str = None

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
        # Note: This should be overridden in the base class AtomicRedisModel, it would allow me to get access to redis key
        self._base_model_link = None
        self._adapter = TypeAdapter(self.__class__)

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


class GenericRedisType(RedisType, ABC):
    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[0] if args else Any

    def create_new_type(self, key):
        inner_original_type = self.find_inner_type(self.original_type)
        type_transformer = RedisTypeTransformer(
            self.sub_field_path(key), self.Meta, type(self._base_model_link)
        )
        new_type = type_transformer[inner_original_type]
        return new_type

    def create_new_value_with_adapter(self, key, value):
        new_type = self.create_new_type(key)
        if new_type is Any:
            return value, TypeAdapter(Any)
        if issubclass(new_type, BaseModel):
            value = value.model_dump()
        adapter = TypeAdapter(new_type)
        normalized_object = adapter.validate_python(value)
        return normalized_object, adapter

    def create_new_value(self, key, value):
        new_value, adapter = self.create_new_value_with_adapter(key, value)
        return new_value

    @classmethod
    @abc.abstractmethod
    def full_serializer(cls, value):
        pass

    @classmethod
    @abc.abstractmethod
    def full_deserializer(cls, value):
        pass

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Extract the generic type argument T from source_type
        element_type = cls.find_inner_type(cls.original_type)

        if element_type is Any:
            # Build schema with both validator and serializer
            python_schema = core_schema.no_info_before_validator_function(
                cls.full_deserializer, handler(cls.original_type)
            )

            return core_schema.no_info_after_validator_function(
                cls,
                python_schema,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    cls.full_serializer,
                    return_schema=core_schema.dict_schema(
                        core_schema.str_schema(), core_schema.str_schema()
                    ),
                ),
            )
        else:
            # Normal serialization for concrete types
            return core_schema.no_info_after_validator_function(
                cls, handler(cls.original_type)
            )
