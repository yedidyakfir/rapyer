import asyncio
import contextlib
import dataclasses
import functools
import uuid
from typing import Self, ClassVar, Any

from pydantic import BaseModel, PrivateAttr
from dataclasses import Field as DCField

from rapyer.config import RedisConfig, RedisFieldConfig
from rapyer.context import _context_var, _context_xx_pipe
from rapyer.errors.base import KeyNotFound
from rapyer.types.base import RedisType
from rapyer.utils import (
    acquire_lock,
    replace_to_redis_types_in_annotation,
    RedisTypeTransformer,
)


class AtomicRedisModel(BaseModel):
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

    def __init_subclass__(cls, **kwargs):
        original_annotations = cls.__annotations__.copy()
        cls.__annotations__ = {
            field_name: replace_to_redis_types_in_annotation(
                field_type, RedisTypeTransformer(field_name, cls.Meta)
            )
            for field_name, field_type in cls.__annotations__.items()
        }
        super().__init_subclass__(**kwargs)

        for attr_name, attr_type in cls.__annotations__.items():
            value = getattr(cls, attr_name)
            if value is None:
                continue

            if isinstance(value, attr_type):
                continue
            orig_type = original_annotations[attr_name]
            redis_type = cls.__annotations__[attr_name]
            if orig_type in cls.Meta.redis_type:
                setattr(cls, attr_name, redis_type(value))
            # Handle Field(default=...)
            elif isinstance(value, DCField):
                if value.default is not dataclasses.MISSING:
                    value.default = redis_type(value.default)
                elif value.default_factory is not dataclasses.MISSING and callable(
                    value.default_factory
                ):
                    test_value = value.default_factory()
                    if isinstance(test_value, attr_type):
                        continue
                    original_factory = value.default_factory
                    value.default_factory = lambda of=original_factory: redis_type(of())

    def __init__(self, _field_config_override=None, **data):
        super().__init__(**data)
        self._field_config_override = _field_config_override
        for field_name in self.model_fields:
            attr = getattr(self, field_name)
            if isinstance(attr, RedisType):
                attr.base_model_link = self

    def is_inner_model(self):
        return self.inst_field_conf.field_path is not None

    async def save(self) -> Self:
        if self.is_inner_model():
            raise RuntimeError("Can only save from top level model")

        model_dump = self.model_dump(mode="json")
        await self.Meta.redis.json().set(self.key, "$", model_dump)
        if self.Meta.ttl is not None:
            await self.Meta.redis.expire(self.key, self.Meta.ttl)
        return self

    async def duplicate(self) -> Self:
        if self.is_inner_model():
            raise RuntimeError("Can only duplicate from top level model")

        duplicated = self.__class__(**self.model_dump())
        await duplicated.save()
        return duplicated

    async def duplicate_many(self, num: int) -> list[Self]:
        if self.is_inner_model():
            raise RuntimeError("Can only duplicate from top level model")

        duplicated_models = [self.__class__(**self.model_dump()) for _ in range(num)]
        await asyncio.gather(*[model.save() for model in duplicated_models])
        return duplicated_models

    @classmethod
    async def get(cls, key: str) -> Self:
        model_dump = await cls.Meta.redis.json().get(key, "$")
        if not model_dump:
            raise KeyNotFound(f"{key} is missing in redis")
        model_dump = model_dump[0]

        instance = cls(**model_dump, should_serialize=True)
        # Extract pk from key format: "ClassName:pk"
        pk = key.split(":", 1)[1]
        instance._pk = pk
        # Update Redis field parameters to use the correct redis_key
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

    @classmethod
    @contextlib.asynccontextmanager
    async def lock_from_key(
        cls, key: str, action: str = "default", save_at_end: bool = False
    ):
        async with acquire_lock(cls.Meta.redis, f"{key}/{action}"):
            redis_model = await cls.get(key)
            yield redis_model
            if save_at_end:
                await redis_model.save()

    @contextlib.asynccontextmanager
    async def lock(self, **kwargs):
        async with self.lock_from_key(self.key, **kwargs) as redis_model:
            self.model_copy(update=redis_model.model_dump())
            yield redis_model

    @contextlib.asynccontextmanager
    async def pipeline(self, ignore_if_deleted: bool = False):
        async with self.Meta.redis.pipeline() as pipe:
            try:
                redis_model = await self.__class__.get(self.key)
                self.model_copy(update=redis_model.model_dump())
            except (TypeError, IndexError):
                if ignore_if_deleted:
                    redis_model = self
                else:
                    raise
            _context_var.set(pipe)
            _context_xx_pipe.set(ignore_if_deleted)
            yield redis_model
            await pipe.execute()
            _context_var.set(None)
            _context_xx_pipe.set(False)

    def __setattr__(self, name: str, value: Any) -> None:
        if value is None:
            super().__setattr__(name, value)
            return

        is_already_at_correct_type = isinstance(value, (RedisType, AtomicRedisModel))
        if name in self.model_fields and not is_already_at_correct_type:
            field_info = self.model_fields[name]
            field_type = field_info.annotation

            if isinstance(field_type, RedisType):
                value = field_type(value)

            # Set the converted Redis instance
            super().__setattr__(name, value)
        else:
            # Use the parent's __setattr__ for all other cases
            super().__setattr__(name, value)

    @classmethod
    def create_redis_type(
        cls,
        redis_type: type["AtomicRedisModel | RedisType"],
        value: Any,
        redis_key: str = None,
        should_serialize: bool = False,
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
            val = redis_type(value, redis_key=redis_key, **saved_kwargs)
            if should_serialize:
                value = val.deserialize_value(val)
                val = redis_type(value, redis_key=redis_key, **saved_kwargs)
            return val
