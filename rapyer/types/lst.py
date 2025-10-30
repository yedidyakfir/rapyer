import json
from typing import TypeVar

from pydantic_core import core_schema
from pydantic_core.core_schema import ValidationInfo, SerializationInfo

from rapyer.types.base import GenericRedisType, RedisType, REDIS_DUMP_FLAG_NAME
from rapyer.types.utils import noop


T = TypeVar("T")


class RedisList(list, GenericRedisType[T]):
    original_type = list

    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        GenericRedisType.__init__(self, *args, **kwargs)

    def sub_field_path(self, field_name: str):
        return f"{self.field_path}[{field_name}]"

    async def load(self) -> list[T]:
        # Get all items from Redis list
        redis_items = await self.client.json().get(self.key, self.field_path)

        if redis_items is None:
            redis_items = []

        # Clear the local list and populate with Redis data using type adapter
        super().clear()
        if redis_items:
            deserialized_items = self._adapter.validate_python(
                redis_items, context={REDIS_DUMP_FLAG_NAME: True}
            )
            super().extend(deserialized_items)
        return list(self)

    def __setitem__(self, key, value):
        new_val = self.create_new_value(key, value)
        self.init_redis_field(f"[{key}]", new_val)
        super().__setitem__(key, new_val)

    async def aappend(self, __object):
        key = len(self)
        new_val = self.create_new_value(key, __object)
        super().append(new_val)

        # Serialize the object for Redis storage using a type adapter
        serialized_object = self._adapter.dump_python(
            [new_val], mode="json", context={REDIS_DUMP_FLAG_NAME: True}
        )
        return await self.client.json().arrappend(
            self.key, self.json_path, *serialized_object
        )

    async def aextend(self, __iterable):
        items = list(__iterable)
        base_idx = len(self)
        redis_items = [
            self.create_new_value(base_idx + i, item) for i, item in enumerate(items)
        ]
        super().extend(redis_items)

        # Convert iterable to list and serialize items using type adapter
        if items:
            normalized_items = self._adapter.validate_python(
                items, context={REDIS_DUMP_FLAG_NAME: True}
            )
            serialized_items = self._adapter.dump_python(
                normalized_items, mode="json", context={REDIS_DUMP_FLAG_NAME: True}
            )
            return await self.client.json().arrappend(
                self.key,
                self.json_path,
                *serialized_items,
            )

        return await noop()

    async def apop(self, index=-1):
        if self:
            super().pop(index)
        arrpop = await self.client.json().arrpop(self.key, self.json_path, index)

        # Handle empty list case
        if arrpop is None or (isinstance(arrpop, list) and len(arrpop) == 0):
            return None

        # Handle case where arrpop returns [None] for an empty list
        if arrpop[0] is None:
            return None
        arrpop = [json.loads(val) for val in arrpop]
        return self._adapter.validate_python(
            arrpop, context={REDIS_DUMP_FLAG_NAME: True}
        )[0]

    async def ainsert(self, index, __object):
        key = len(self)
        new_val = self.create_new_value(key, __object)
        super().insert(index, new_val)

        # Serialize the object for Redis storage using a type adapter
        normalized_object = self._adapter.validate_python(
            [__object], context={REDIS_DUMP_FLAG_NAME: True}
        )
        serialized_object = self._adapter.dump_python(
            normalized_object, mode="json", context={REDIS_DUMP_FLAG_NAME: True}
        )
        return await self.client.json().arrinsert(
            self.key, self.json_path, index, *serialized_object
        )

    async def aclear(self):
        # Clear local list
        super().clear()

        # Clear Redis list
        return await self.client.json().set(self.key, self.json_path, [])

    def clone(self):
        return [v.clone() if isinstance(v, RedisType) else v for v in self]

    def iterate_items(self):
        keys = [f"[{i}]" for i in range(len(self))]
        return zip(keys, self)

    @classmethod
    def full_serializer(cls, value, info: SerializationInfo):
        ctx = info.context or {}
        is_redis_data = ctx.get(REDIS_DUMP_FLAG_NAME)
        return [
            cls.serialize_unknown(item) if is_redis_data else item for item in value
        ]

    @classmethod
    def full_deserializer(cls, value, info: ValidationInfo):
        ctx = info.context or {}
        is_redis_data = ctx.get(REDIS_DUMP_FLAG_NAME)

        if isinstance(value, list):
            return [
                cls.deserialize_unknown(item) if is_redis_data else item
                for item in value
            ]
        return value

    @classmethod
    def schema_for_unknown(cls):
        core_schema.list_schema(core_schema.str_schema())
