import asyncio
import contextlib
import functools
import uuid
from typing import Self, ClassVar, Any

from pydantic import BaseModel, PrivateAttr, ConfigDict, TypeAdapter
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from rapyer.config import RedisConfig, RedisFieldConfig
from rapyer.context import _context_var, _context_xx_pipe
from rapyer.errors.base import KeyNotFound
from rapyer.types.base import RedisType, BaseRedisType, RedisTypeTransformer
from rapyer.utils import (
    acquire_lock,
    replace_to_redis_types_in_annotation,
    find_first_type_in_annotation,
    convert_field_factory_type,
    get_all_annotations,
)


class AtomicRedisModel(BaseModel):
    _pk: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))
    Meta: ClassVar[RedisConfig] = RedisConfig()
    field_config: ClassVar[RedisFieldConfig] = RedisFieldConfig()
    _base_model_link: Self = PrivateAttr(default=None)
    model_config = ConfigDict(validate_assignment=True)

    @property
    def pk(self):
        return self._pk

    @pk.setter
    def pk(self, value: str):
        self._pk = value

    @classmethod
    def class_key_initials(cls):
        return cls.__name__

    @property
    def key_initials(self):
        return self.class_key_initials()

    @property
    def key(self):
        if self._base_model_link:
            return self._base_model_link.key
        return f"{self.key_initials}:{self.pk}"

    def __init_subclass__(cls, **kwargs):
        original_annotations = get_all_annotations(
            cls, exclude_classes=[AtomicRedisModel]
        )
        field_path = cls.field_config.field_path
        new_annotations = {
            field_name: replace_to_redis_types_in_annotation(
                field_type,
                RedisTypeTransformer(full_field_path, cls.Meta, AtomicRedisModel),
            )
            for field_name, field_type in original_annotations.items()
            if (
                full_field_path := (
                    f"{field_path}.{field_name}" if field_path else field_name
                )
            )
        }
        cls.__annotations__.update(new_annotations)
        super().__init_subclass__(**kwargs)

        for attr_name, attr_type in cls.__annotations__.items():
            if original_annotations[attr_name] == attr_type:
                continue
            value = getattr(cls, attr_name, None)
            if value is None:
                continue

            real_type = find_first_type_in_annotation(attr_type)

            if isinstance(value, real_type):
                continue
            redis_type = cls.__annotations__[attr_name]
            redis_type: type[BaseRedisType]
            adapter = TypeAdapter(redis_type)

            # Handle Field(default=...)
            if isinstance(value, FieldInfo):
                if value.default != PydanticUndefined:
                    value.default = adapter.validate_python(value.default)
                elif value.default_factory != PydanticUndefined and callable(
                    value.default_factory
                ):
                    test_value = value.default_factory()
                    if isinstance(test_value, real_type):
                        continue
                    original_factory = value.default_factory
                    validate_from_adapter = functools.partial(
                        convert_field_factory_type, original_factory, adapter
                    )
                    value.default_factory = validate_from_adapter
            else:
                setattr(cls, attr_name, adapter.validate_python(value))

    def __init__(self, _base_model_link=None, **data):
        data = {
            k: (
                v.model_dump()
                if isinstance(v, BaseModel)
                and not isinstance(v, self.__annotations__[k])
                else v
            )
            for k, v in data.items()
        }
        super().__init__(**data)
        self._base_model_link = _base_model_link
        for field_name in self.model_fields:
            attr = getattr(self, field_name)
            if isinstance(attr, RedisType) or isinstance(attr, AtomicRedisModel):
                attr._base_model_link = _base_model_link or self

    def is_inner_model(self):
        return self.field_config.field_path is not None

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
        # Extract pk from the key format: "ClassName:pk"
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
            self.__dict__.update(redis_model.model_dump(exclude_unset=True))
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
        super().__setattr__(name, value)
        if value is not None:
            attr = getattr(self, name)
            if isinstance(attr, RedisType):
                attr._base_model_link = self
