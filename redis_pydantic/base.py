import asyncio
import contextlib
import dataclasses
import uuid
from typing import get_origin, Self, ClassVar, Any

import redis
from pydantic import BaseModel, PrivateAttr
from redis.asyncio import Redis

from redis_pydantic.types import ALL_TYPES, create_serializer
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
        # Handle generic types
        origin_type = get_origin(type_) or type_

        # Check if this type has a Redis equivalent
        if origin_type in cls.Meta.redis_type:
            redis_type_class = cls.Meta.redis_type[origin_type]

            # If it's a GenericRedisType, create its serializer
            if issubclass(redis_type_class, GenericRedisType):
                return [
                    redis_type_class,
                    {"serializer_creator": create_serializer, "full_type": type_},
                ]
            else:
                return [redis_type_class, {}]
        elif issubclass(type_, BaseRedisModel):
            field_conf = RedisFieldConfig(
                field_path=field_name, override_class_name=cls.key_initials()
            )
            new_base_redis_type = type(
                f"{field_name.title()}{type_.__name__}",
                (type_,),
                dict(field_config=field_conf),
            )
            return [new_base_redis_type, {}]
        elif issubclass(type_, BaseModel):
            field_conf = RedisFieldConfig(
                field_path=field_name, override_class_name=cls.key_initials()
            )
            new_base_model_type = type(
                f"Redis{type_.__name__}",
                (type_, BaseRedisModel),
                dict(field_config=field_conf),
            )
            return [new_base_model_type, {}]
        else:
            raise RuntimeError(f"{type_} not supported by RedisPydantic")

    @classmethod
    def create_redis_type(
        cls, redis_type_def: list, value: Any, redis_key: str = None, **kwargs
    ):
        redis_type = redis_type_def[0]
        saved_kwargs = redis_type_def[1]

        # Handle nested models - convert user model to Redis model
        if isinstance(value, BaseModel):
            pk = redis_key.split(":", 1)[1]
            model_data = value.model_dump()
            instance = redis_type(**model_data, **saved_kwargs)
            instance.pk = pk
            return instance
        else:
            return redis_type(value, **kwargs, redis_key=redis_key, **saved_kwargs)

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize Redis fields after Pydantic initialization
        for field_name, type_definitions in self._redis_field_mapping.items():
            # Get the current value (from Pydantic initialization)
            current_value = getattr(self, field_name, None)
            if current_value is None:
                continue

            full_field_path = (
                f"{self.field_config.field_path}.{field_name}"
                if self.field_config.field_path
                else field_name
            )
            redis_instance = self.create_redis_type(
                value=current_value,
                redis_type_def=type_definitions,
                redis_key=self.key,
                field_path=full_field_path,
                redis=self.Meta.redis,
            )

            # Set it directly on the instance
            object.__setattr__(self, field_name, redis_instance)

    def __setattr__(self, name: str, value: Any) -> None:
        if value is None:
            super().__setattr__(name, value)
            return

        is_already_at_correct_type = isinstance(value, (RedisType, BaseRedisModel))
        has_redis_type = name in self._redis_field_mapping
        if has_redis_type and not is_already_at_correct_type:
            type_definitions = self._redis_field_mapping[name]
            full_field_path = (
                f"{self.field_config.field_path}.{name}"
                if self.field_config.field_path
                else name
            )

            redis_instance = self.create_redis_type(
                value=value,
                redis_type_def=type_definitions,
                redis_key=self.key,
                field_path=full_field_path,
                redis=self.Meta.redis,
            )

            # Set the converted Redis instance
            super().__setattr__(name, redis_instance)
        else:
            # Use the parent's __setattr__ for all other cases
            super().__setattr__(name, value)

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

    async def load(self):
        await asyncio.gather(
            *[getattr(self, field_name).load() for field_name in self.model_dump()]
        )

    @contextlib.asynccontextmanager
    async def lock(self, action: str = "default"):
        async with acquire_lock(self.Meta.redis, f"{self.key}/{action}"):
            redis_model = await self.__class__.get(self.key)
            self.model_copy(update=redis_model.model_dump())
            yield redis_model
            await redis_model.save()


# TODO - steps
# 5. update the redis types, with __get__ etc
# 5. add pipeline context - change the load to pipeline rather than lock
# 6. check that using my types explicit works
# TODO - add foreign key - for deletion
# TODO - when setting a field, update with inner type (model.lst = []...)
# TODO - allow dict serializer for key and value
