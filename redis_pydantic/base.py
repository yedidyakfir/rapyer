import asyncio
import json
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, get_origin, get_args, Self, Union, Annotated

import redis
from pydantic import BaseModel, Field, PrivateAttr
from redis.asyncio.client import Pipeline

from redis_pydantic.types import ALL_TYPES

DEFAULT_CONNECTION = "redis://localhost:6379/0"


def create_field_key(key: str, field_name: str) -> str:
    return f"{key}/{field_name}"


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
        self.private_name = f"_redis_{field_name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        # Get or create the Redis type instance
        if not hasattr(obj, self.private_name):
            # Prepare initial value
            initial_value = []
            if self.default_value is not None:
                if callable(self.default_value):
                    initial_value = self.default_value()
                else:
                    initial_value = self.default_value

            # Create instance with current parameters and initial value
            redis_instance = self.redis_type_class(
                initial_value,
                redis_key=obj.key,
                field_path=self.field_name,
                redis=obj.Meta.redis,
            )
            setattr(obj, self.private_name, redis_instance)

        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        # Create new Redis type instance with the value
        initial_value = value if value is not None else []
        redis_instance = self.redis_type_class(
            initial_value,
            redis_key=obj.key,
            field_path=self.field_name,
            redis=obj.Meta.redis,
        )
        setattr(obj, self.private_name, redis_instance)

    def __delete__(self, obj):
        if hasattr(obj, self.private_name):
            delattr(obj, self.private_name)


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

            # Handle generic types like list[str] by checking the origin
            origin_type = get_origin(actual_type) or actual_type

            # Check if this type should be replaced with a Redis type
            if origin_type in cls.Meta.redis_type:
                redis_type_class = cls.Meta.redis_type[origin_type]
                cls._redis_field_mapping[field_name] = redis_type_class

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize Redis fields after Pydantic initialization
        for field_name, redis_type_class in getattr(
            self.__class__, "_redis_field_mapping", {}
        ).items():
            # Get the current value (from Pydantic initialization)
            current_value = getattr(self, field_name, [])

            # Create Redis type instance
            redis_instance = redis_type_class(
                current_value,
                redis_key=self.key,
                field_path=field_name,
                redis=self.Meta.redis,
            )

            # Set it directly on the instance
            object.__setattr__(self, field_name, redis_instance)

    async def save(self) -> Self:
        model_dump = self.model_dump(exclude=["_pk"])
        await self.Meta.redis.json().set(self.key, "$", model_dump)
        return self


# TODO - return if update was successful
# TODO - get the values after incrby and after lpush to store it
# TODO - imporve get
# TODO - move to metaclass
# TODO - create wrapper for each supported type
# TODO - add flag to put multiple fields in one key
# TODO - allow foreign keys
# TODO - how to handle list of models?
# TODO - create a lock as context manager, with updated self - also it should accept different actions
