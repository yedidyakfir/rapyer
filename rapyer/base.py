import asyncio
import contextlib
import uuid
from typing import Self, ClassVar, Any, AsyncGenerator

from pydantic import (
    BaseModel,
    PrivateAttr,
    ConfigDict,
    model_validator,
)

from rapyer.config import RedisConfig
from rapyer.context import _context_var, _context_xx_pipe
from rapyer.errors.base import KeyNotFound
from rapyer.meta import RapyerMeta
from rapyer.types.base import RedisType, REDIS_DUMP_FLAG_NAME
from rapyer.utils.redis import acquire_lock, update_keys_in_pipeline


class AtomicRedisModel(BaseModel, metaclass=RapyerMeta):
    _pk: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))
    _base_model_link: Self | RedisType = PrivateAttr(default=None)

    Meta: ClassVar[RedisConfig] = RedisConfig()
    _field_name: str = PrivateAttr(default="")
    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    @property
    def pk(self):
        return self._pk

    @pk.setter
    def pk(self, value: str):
        self._pk = value

    @property
    def field_name(self):
        return self._field_name

    @field_name.setter
    def field_name(self, value: str):
        self._field_name = value

    @property
    def field_path(self):
        if not self._base_model_link:
            return self.field_name
        parent_field_path = self._base_model_link.field_path
        if parent_field_path:
            return f"{parent_field_path}{self.field_name}"
        return self.field_name

    @property
    def json_path(self):
        field_path = self.field_path
        return f"${field_path}" if field_path else "$"

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
        super().__init_subclass__(**kwargs)

        # Update the redis model list for initialization
        REDIS_MODELS.append(cls)

    def is_inner_model(self) -> bool:
        return bool(self.field_name)

    async def save(self) -> Self:
        model_dump = self.model_dump(mode="json", context={REDIS_DUMP_FLAG_NAME: True})
        await self.Meta.redis.json().set(self.key, self.json_path, model_dump)
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

    def update(self, **kwargs):
        for field_name, value in kwargs.items():
            setattr(self, field_name, value)

    async def aupdate(self, **kwargs):
        self.update(**kwargs)

        # Only serialize the updated fields using the include parameters
        serialized_fields = self.model_dump(
            mode="json",
            context={REDIS_DUMP_FLAG_NAME: True},
            include=set(kwargs.keys()),
        )
        json_path_kwargs = {
            f"{self.json_path}.{field_name}": serialized_fields[field_name]
            for field_name in kwargs.keys()
        }

        async with self.Meta.redis.pipeline() as pipe:
            update_keys_in_pipeline(pipe, self.key, **json_path_kwargs)
            await pipe.execute()

    @classmethod
    async def get(cls, key: str) -> Self:
        model_dump = await cls.Meta.redis.json().get(key, "$")
        if not model_dump:
            raise KeyNotFound(f"{key} is missing in redis")
        model_dump = model_dump[0]

        instance = cls.model_validate(model_dump, context={REDIS_DUMP_FLAG_NAME: True})
        # Extract pk from the key format: "ClassName:pk"
        pk = key.split(":", 1)[1]
        instance._pk = pk
        # Update Redis field parameters to use the correct redis_key
        return instance

    async def load(self) -> Self:
        model_dump = await self.Meta.redis.json().get(self.key, self.json_path)
        if not model_dump:
            raise KeyNotFound(f"{self.key} is missing in redis")
        model_dump = model_dump[0]
        instance = self.__class__(**model_dump)
        instance._pk = self._pk
        instance._base_model_link = self._base_model_link
        return instance

    @classmethod
    async def delete_by_key(cls, key: str) -> bool:
        client = _context_var.get() or cls.Meta.redis
        return await client.delete(key) == 1

    async def delete(self):
        if self.is_inner_model():
            raise RuntimeError("Can only delete from inner model")
        return await self.delete_by_key(self.key)

    @classmethod
    @contextlib.asynccontextmanager
    async def lock_from_key(
        cls, key: str, action: str = "default", save_at_end: bool = False
    ) -> AsyncGenerator[Self, None]:
        async with acquire_lock(cls.Meta.redis, f"{key}/{action}"):
            redis_model = await cls.get(key)
            yield redis_model
            if save_at_end:
                await redis_model.save()

    @contextlib.asynccontextmanager
    async def lock(
        self, action: str = "default", save_at_end: bool = False
    ) -> AsyncGenerator[Self, None]:
        async with self.lock_from_key(self.key, action, save_at_end) as redis_model:
            unset_fields = {
                k: redis_model.__dict__[k] for k in redis_model.model_fields_set
            }
            self.__dict__.update(unset_fields)
            yield redis_model

    @contextlib.asynccontextmanager
    async def pipeline(
        self, ignore_if_deleted: bool = False
    ) -> AsyncGenerator[Self, None]:
        async with self.Meta.redis.pipeline() as pipe:
            try:
                redis_model = await self.__class__.get(self.key)
                unset_fields = {
                    k: redis_model.__dict__[k] for k in redis_model.model_fields_set
                }
                self.__dict__.update(unset_fields)
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
        if name not in self.__annotations__ or value is None:
            super().__setattr__(name, value)
            return

        super().__setattr__(name, value)
        if value is not None:
            attr = getattr(self, name)
            if isinstance(attr, RedisType):
                attr._base_model_link = self

    def __eq__(self, other):
        if not isinstance(other, BaseModel):
            return False
        if self.__dict__ == other.__dict__:
            return True
        else:
            return super().__eq__(other)

    @model_validator(mode="before")
    @classmethod
    def validate_sub_model(cls, values):
        if isinstance(values, BaseModel) and not isinstance(values, cls):
            return values.model_dump()
        return values

    @model_validator(mode="after")
    def assign_fields_links(self):
        for field_name in self.model_fields:
            attr = getattr(self, field_name)
            if isinstance(attr, RedisType) or isinstance(attr, AtomicRedisModel):
                attr._base_model_link = self
        return self


REDIS_MODELS: list[type[AtomicRedisModel]] = []
