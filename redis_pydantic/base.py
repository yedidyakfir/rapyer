import uuid
from typing import Any, get_origin, get_args, Self, Union

import redis
from pydantic import BaseModel, PrivateAttr

from redis_pydantic.types import ALL_TYPES
from redis_pydantic.types.base import GenericRedisType, RedisType

DEFAULT_CONNECTION = "redis://localhost:6379/0"


def get_actual_type(annotation: Any) -> Any:
    """Extract the actual type from Optional/Union types."""
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        # Handle Optional[T] which is Union[T, None]
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
        return annotation  # Return as-is for complex Union types
    return annotation


class RedisFieldDescriptor:
    """Descriptor that creates Redis type instances with proper parameters."""

    def __init__(self, redis_type_class, field_name, default_value=None):
        self.redis_type_class = redis_type_class
        self.field_name = field_name
        self.default_value = default_value


class BaseRedisModel(BaseModel):
    _pk: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))

    class Meta:
        redis = redis.asyncio.from_url(DEFAULT_CONNECTION)
        redis_type: dict[str, type] = ALL_TYPES

    @property
    def pk(self):
        return self._pk

    @pk.setter
    def pk(self, value: str):
        self._pk = value
        self._update_redis_field_parameters()

    @property
    def key(self):
        return f"{self.__class__.__name__}:{self.pk}"

    def _update_redis_field_parameters(self):
        """Update Redis field parameters when key or redis connection changes."""
        for field_name in getattr(self.__class__, "_redis_field_mapping", {}):
            if hasattr(self, field_name):
                redis_instance = getattr(self, field_name)
                if hasattr(redis_instance, "redis_key") and hasattr(
                    redis_instance, "redis"
                ):
                    redis_instance.redis_key = self.key
                    redis_instance.redis = self.Meta.redis

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Store Redis field mappings for later use
        cls._redis_field_mapping = {}

        # Replace field types with Redis types and create descriptors
        for field_name, field_type in cls.__annotations__.items():
            actual_type = get_actual_type(field_type)
            resolved_inner_type = cls._resolve_redis_type(actual_type)
            cls._redis_field_mapping[field_name] = resolved_inner_type

    @classmethod
    def _resolve_redis_type(cls, type_):
        """Recursively resolve a type to its Redis equivalent."""
        # Handle generic types
        origin_type = get_origin(type_) or type_

        # Check if this type has a Redis equivalent
        if origin_type in cls.Meta.redis_type:
            redis_type_class = cls.Meta.redis_type[origin_type]

            # If it's a GenericRedisType, recursively resolve its inner type
            if issubclass(redis_type_class, GenericRedisType):
                inner_type = redis_type_class.find_inner_type(type_)
                resolved_inner_type = cls._resolve_redis_type(inner_type)
                return {redis_type_class: {"inner_type": resolved_inner_type}}
            else:
                return {redis_type_class: {}}
        else:
            raise RuntimeError(f"{type_} not supported by RedisPydantic")

    @classmethod
    def create_redis_type(cls, redis_mapping: dict, value=None, **kwargs):
        redis_type = list(redis_mapping.keys())[0]
        redis_type_additional_params = redis_mapping[redis_type]
        saved_kwargs = {
            key: (cls.create_redis_type(value))
            for key, value in redis_type_additional_params.items()
        }
        return redis_type(value, **kwargs, **saved_kwargs)

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize Redis fields after Pydantic initialization
        for field_name, redis_mapping in self.__class__._redis_field_mapping.items():
            # Get the current value (from Pydantic initialization)
            current_value = getattr(self, field_name, None)
            redis_instance = self.create_redis_type(
                value=current_value,
                redis_mapping=redis_mapping,
                redis_key=self.key,
                field_path=field_name,
                redis=self.Meta.redis,
            )

            # Set it directly on the instance
            object.__setattr__(self, field_name, redis_instance)

    async def save(self) -> Self:
        model_dump = self.redis_dump()
        await self.Meta.redis.json().set(self.key, "$", model_dump)
        return self

    def redis_dump(self):
        model_dump = self.model_dump(exclude=["_pk"])
        # Override Redis field values with their serialized versions
        for field_name in self.model_fields:
            if hasattr(self, field_name):
                redis_field = getattr(self, field_name)
                if isinstance(redis_field, RedisType):
                    model_dump[field_name] = redis_field.serialize_value(redis_field)
        return model_dump


# TODO - return if update was successful
# TODO - get the values after incrby and after lpush to store it
# TODO - imporve get
# TODO - move to metaclass
# TODO - create wrapper for each supported type
# TODO - add flag to put multiple fields in one key
# TODO - allow foreign keys
# TODO - how to handle list of models?
# TODO - create a lock as context manager, with updated self - also it should accept different actions
# TODO - add foreign key - for deletion


# TODO - steps
#  1. finish list + add ttl
#  2. finish dict + add ttl
#  3. create default class setter + add ttl
#  4. create serializer for primitives
#  5. create tests to check
#  6. Create for pydantic + add ttl
#  7. create lock actions context
#  8. create pipeline actions context
#  9. create for nested
