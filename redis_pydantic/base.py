import asyncio
import contextlib
import dataclasses
import functools
import uuid
from typing import get_origin, Self, ClassVar, Any

from pydantic import BaseModel, PrivateAttr

from redis_pydantic.config import RedisConfig, RedisFieldConfig
from redis_pydantic.context import _context_var
from redis_pydantic.types import create_serializer
from redis_pydantic.types.base import GenericRedisType, RedisType
from redis_pydantic.utils import (
    acquire_lock,
    get_public_instance_annotations,
    get_actual_type,
)


class BaseRedisModel(BaseModel):
    _pk: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))
    Meta: ClassVar[RedisConfig] = RedisConfig()
    field_config: ClassVar[RedisFieldConfig] = RedisFieldConfig()
    _field_config_override: RedisFieldConfig = None

    @property
    def pk(self):
        return self._pk

    @pk.setter
    def pk(self, value: str):
        self._pk = value
        self._update_redis_field_parameters()

    @functools.cached_property
    def inst_field_conf(self) -> RedisFieldConfig:
        class_conf = dataclasses.asdict(self.field_config)
        inst_conf = (
            dataclasses.asdict(self._field_config_override)
            if self._field_config_override
            else {}
        )
        inst_conf = {k: v for k, v in inst_conf.items() if v is not None}
        conf = class_conf | inst_conf
        return RedisFieldConfig(**conf)

    @classmethod
    def class_key_initials(cls):
        return cls.field_config.override_class_name or cls.__name__

    @property
    def key_initials(self):
        return self.inst_field_conf.override_class_name or self.class_key_initials()

    @property
    def key(self):
        return f"{self.key_initials}:{self.pk}"

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
                    {
                        "serializer_creator": create_serializer,
                        "full_type": type_,
                        "inst_init": cls.create_redis_type,
                        "type_creator": cls._resolve_redis_type,
                    },
                ]
            else:
                return [redis_type_class, {}]
        elif issubclass(type_, BaseRedisModel):
            field_conf = RedisFieldConfig(
                field_path=field_name, override_class_name=cls.class_key_initials()
            )
            return [type_, {"_field_config_override": field_conf}]
        elif issubclass(type_, BaseModel):
            field_conf = RedisFieldConfig(
                field_path=field_name, override_class_name=cls.class_key_initials()
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
        cls,
        redis_type: type["BaseRedisModel | RedisType"],
        value: Any,
        redis_key: str = None,
        **saved_kwargs,
    ):
        # Handle nested models - convert user model to Redis model
        if isinstance(value, BaseModel):
            pk = redis_key.split(":", 1)[1]
            model_data = value.model_dump()
            instance = redis_type(**model_data, **saved_kwargs)
            instance.pk = pk
            return instance
        else:
            return redis_type(value, redis_key=redis_key, **saved_kwargs)

    def __init__(self, _field_config_override=None, **data):
        super().__init__(**data)
        self._field_config_override = _field_config_override

        # Initialize Redis fields after Pydantic initialization
        for field_name, type_definitions in self._redis_field_mapping.items():
            # Get the current value (from Pydantic initialization)
            current_value = getattr(self, field_name, None)
            if current_value is None:
                continue

            full_field_path = (
                f"{self.inst_field_conf.field_path}.{field_name}"
                if self.inst_field_conf.field_path
                else field_name
            )
            redis_instance = self.create_redis_type(
                redis_type=type_definitions[0],
                value=current_value,
                redis_key=self.key,
                field_path=full_field_path,
                redis=self.Meta.redis,
                **type_definitions[1],
            )

            # Set it directly on the instance
            object.__setattr__(self, field_name, redis_instance)

    def is_ineer_model(self):
        return self.inst_field_conf.field_path is not None

    def __setattr__(self, name: str, value: Any) -> None:
        if value is None:
            super().__setattr__(name, value)
            return

        is_already_at_correct_type = isinstance(value, (RedisType, BaseRedisModel))
        has_redis_type = name in self._redis_field_mapping
        if has_redis_type and not is_already_at_correct_type:
            type_definitions = self._redis_field_mapping[name]
            full_field_path = (
                f"{self.inst_field_conf.field_path}.{name}"
                if self.inst_field_conf.field_path
                else name
            )

            redis_instance = self.create_redis_type(
                redis_type=type_definitions[0],
                value=value,
                redis_key=self.key,
                field_path=full_field_path,
                redis=self.Meta.redis,
                **type_definitions[1],
            )

            # Set the converted Redis instance
            super().__setattr__(name, redis_instance)
        else:
            # Use the parent's __setattr__ for all other cases
            super().__setattr__(name, value)

    async def save(self) -> Self:
        if self.is_ineer_model():
            raise RuntimeError("Can only save from top level model")

        model_dump = self.redis_dump()
        await self.Meta.redis.json().set(self.key, "$", model_dump)
        if self.Meta.ttl is not None:
            await self.Meta.redis.expire(self.key, self.Meta.ttl)
        return self

    async def duplicate(self) -> Self:
        if self.is_ineer_model():
            raise RuntimeError("Can only duplicate from top level model")

        duplicated = self.__class__(**self.model_dump())
        await duplicated.save()
        return duplicated

    async def duplicate_many(self, num: int) -> list[Self]:
        if self.is_ineer_model():
            raise RuntimeError("Can only duplicate from top level model")

        duplicated_models = [self.__class__(**self.model_dump()) for _ in range(num)]
        await asyncio.gather(*[model.save() for model in duplicated_models])
        return duplicated_models

    @classmethod
    async def get(cls, key: str) -> Self:
        model_dump = await cls.Meta.redis.json().get(key, "$")
        instance = cls(**model_dump[0])
        # Extract pk from key format: "ClassName:pk"
        pk = key.split(":", 1)[1]
        instance._pk = pk
        # Update Redis field parameters to use the correct redis_key
        instance._update_redis_field_parameters()
        return instance

    @classmethod
    async def try_delete(cls, key: str) -> bool:
        client = _context_var.get() or cls.Meta.redis
        return await client.delete(key) == 1

    async def delete(self):
        client = _context_var.get() or self.Meta.redis
        return await client.delete(self.key)

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

    @contextlib.asynccontextmanager
    async def pipeline(self):
        async with self.Meta.redis.pipeline() as pipe:
            redis_model = await self.__class__.get(self.key)
            self.model_copy(update=redis_model.model_dump())
            _context_var.set(pipe)
            yield redis_model
            await pipe.execute()
            _context_var.set(None)
