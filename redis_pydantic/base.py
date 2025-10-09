import contextlib
import dataclasses
import uuid
from typing import get_origin, Self, ClassVar

import redis
from pydantic import BaseModel, PrivateAttr
from redis.asyncio import Redis

from redis_pydantic.types import ALL_TYPES
from redis_pydantic.types.base import GenericRedisType, RedisType
from redis_pydantic.utils import (
    acquire_lock,
    get_public_instance_annotations,
    get_actual_type,
)

DEFAULT_CONNECTION = "redis://localhost:6379/0"


@dataclasses.dataclass
class RedisConfig:
    redis: Redis = dataclasses.field(
        default_factory=lambda: redis.asyncio.from_url(DEFAULT_CONNECTION)
    )
    redis_type: dict[str, type] = dataclasses.field(default_factory=lambda: ALL_TYPES)
    ttl: int | None = None


@dataclasses.dataclass
class RedisFieldConfig:
    field_path: str = ""
    override_class_name: str = ""


class BaseRedisModel(BaseModel):
    _pk: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))
    Meta: ClassVar[RedisConfig] = RedisConfig()
    field_config: ClassVar[RedisFieldConfig] = RedisFieldConfig()

    @property
    def pk(self):
        return self._pk

    @pk.setter
    def pk(self, value: str):
        self._pk = value
        self._update_redis_field_parameters()

    @classmethod
    def key_initials(cls):
        return cls.field_config.override_class_name or cls.__name__

    @property
    def key(self):
        return f"{self.key_initials()}:{self.pk}"

    def _update_redis_field_parameters(self):
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if isinstance(value, RedisType):
                value.redis_key = self.key
            elif isinstance(value, BaseRedisModel):
                value.pk = self.pk

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Store Redis field mappings for later use
        cls._redis_field_mapping = {}
        full_annotation = get_public_instance_annotations(cls)

        # Replace field types with Redis types and create descriptors
        for field_name, field_type in full_annotation.items():
            actual_type = get_actual_type(field_type)
            full_field_name = (
                f"{cls.field_config.field_path}.{field_name}"
                if cls.field_config.field_path
                else field_name
            )
            resolved_inner_type = cls._resolve_redis_type(full_field_name, actual_type)
            cls._redis_field_mapping[field_name] = resolved_inner_type

    @classmethod
    def _resolve_redis_type(cls, field_name, type_):
        """Recursively resolve a type to its Redis equivalent."""
        # Handle generic types
        origin_type = get_origin(type_) or type_

        # Check if this type has a Redis equivalent
        if origin_type in cls.Meta.redis_type:
            redis_type_class = cls.Meta.redis_type[origin_type]

            # If it's a GenericRedisType, recursively resolve its inner type
            if issubclass(redis_type_class, GenericRedisType):
                inner_type = redis_type_class.find_inner_type(type_)
                resolved_inner_type = cls._resolve_redis_type(field_name, inner_type)
                return {redis_type_class: {"inner_type": resolved_inner_type}}
            else:
                return {redis_type_class: {}}
        elif issubclass(type_, BaseRedisModel):
            field_conf = RedisFieldConfig(
                field_path=field_name, override_class_name=cls.key_initials()
            )
            return {type_: {"field_config": field_conf}}
        elif issubclass(type_, BaseModel):
            field_conf = RedisFieldConfig(
                field_path=field_name, override_class_name=cls.key_initials()
            )
            new_base_model_type = type(
                f"Redis{type_.__name__}",
                (type_, BaseRedisModel),
                dict(field_config=field_conf),
            )
            return {new_base_model_type: {}}
        else:
            raise RuntimeError(f"{type_} not supported by RedisPydantic")

    @classmethod
    def create_redis_type(cls, redis_mapping: dict, value=None, **kwargs):
        redis_type = list(redis_mapping.keys())[0]
        redis_type_additional_params = redis_mapping[redis_type]
        saved_kwargs = {
            key: (cls.create_redis_type(redis_mapping=value, **kwargs))
            for key, value in redis_type_additional_params.items()
        }

        # Handle nested models - convert user model to Redis model
        if (
            value is not None
            and isinstance(value, BaseModel)
            and not isinstance(value, BaseRedisModel)
        ):
            redis_key = kwargs.get("redis_key")
            pk = redis_key.split(":", 1)[1]
            model_data = value.model_dump()
            instance = redis_type(**model_data, **saved_kwargs)
            instance.pk = pk
            return instance
        elif value is not None and isinstance(value, BaseRedisModel):
            # Handle case where value is already a BaseRedisModel
            redis_key = kwargs.get("redis_key")
            pk = redis_key.split(":", 1)[1]
            model_data = value.model_dump()
            instance = redis_type(**model_data, **saved_kwargs)
            instance.pk = pk
            return instance
        elif value is None:
            # Handle case where no value is provided (default initialization)
            return redis_type(**kwargs, **saved_kwargs)
        else:
            return redis_type(value, **kwargs, **saved_kwargs)

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize Redis fields after Pydantic initialization
        for field_name, redis_mapping in self._redis_field_mapping.items():
            # Get the current value (from Pydantic initialization)
            current_value = getattr(self, field_name, None)
            full_field_path = (
                f"{self.field_config.field_path}.{field_name}"
                if self.field_config.field_path
                else field_name
            )
            redis_instance = self.create_redis_type(
                value=current_value,
                redis_mapping=redis_mapping,
                redis_key=self.key,
                field_path=full_field_path,
                redis=self.Meta.redis,
            )

            # Set it directly on the instance
            object.__setattr__(self, field_name, redis_instance)

    async def save(self) -> Self:
        model_dump = self.redis_dump()
        await self.Meta.redis.json().set(self.key, "$", model_dump)
        if self.Meta.ttl is not None:
            await self.Meta.redis.expire(self.key, self.Meta.ttl)
        return self

    @classmethod
    async def get(cls, key: str) -> Self:
        model_dump = await cls.Meta.redis.json().get(key, "$")
        instance = cls(**model_dump[0])
        # Extract pk from key format: "ClassName:pk"
        pk = key.split(":", 1)[1]
        instance._pk = pk
        return instance

    def redis_dump(self):
        model_dump = self.model_dump(exclude=["_pk"])
        # Override Redis field values with their serialized versions
        for field_name in self.model_fields:
            if hasattr(self, field_name):
                redis_field = getattr(self, field_name)
                if isinstance(redis_field, RedisType):
                    model_dump[field_name] = redis_field.serialize_value(redis_field)
        return model_dump

    @contextlib.asynccontextmanager
    async def lock(self, action: str = "default"):
        async with acquire_lock(self.Meta.redis, f"{self.key}/{action}"):
            redis_model = await self.__class__.get(self.key)
            self.model_copy(update=redis_model.model_dump())
            yield redis_model
            await redis_model.save()


# TODO - steps
# 2. check models nested of redis models
# 3. split models and serializer
# 4. update the redis types with serializer and inner models
# 5. update the redis types, with __get__ etc
# 5. add pipeline context
# TODO - add foreign key - for deletion
# TODO - when setting a field, update with inner type (model.lst = []...)
