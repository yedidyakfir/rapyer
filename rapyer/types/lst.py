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

    def create_new_values(self, keys, values):
        new_values = self._adapter.validate_python(values)
        for key, value in zip(keys, new_values):
            self.init_redis_field(f"[{key}]", value)
        return new_values

    def create_new_value(self, key, value):
        new_val = self.create_new_values([key], [value])[0]
        return new_val

    def __setitem__(self, key, value):
        new_val = self.create_new_value(key, value)
        super().__setitem__(key, new_val)

    def __iadd__(self, other):
        self.extend(other)
        return self

    def append(self, __object):
        key = len(self)
        new_val = self.create_new_value(key, __object)
        return super().append(new_val)

    def extend(self, new_lst):
        new_keys = range(len(self), len(self) + len(new_lst))
        new_vals = self.create_new_values(list(new_keys), new_lst)
        return super().extend(new_vals)

    def insert(self, index, __object):
        new_val = self.create_new_value(index, __object)
        return super().insert(index, new_val)

    async def aappend(self, __object):
        super().append(__object)

        # Serialize the object for Redis storage using a type adapter
        serialized_object = self._adapter.dump_python(
            [__object], mode="json", context={REDIS_DUMP_FLAG_NAME: True}
        )
        return await self.client.json().arrappend(
            self.key, self.json_path, *serialized_object
        )

    async def aextend(self, __iterable):
        items = list(__iterable)
        self.extend(items)

        # Convert iterable to list and serialize items using type adapter
        if items:
            # normalized_items = self._adapter.validate_python(items)
            serialized_items = self._adapter.dump_python(
                items, mode="json", context={REDIS_DUMP_FLAG_NAME: True}
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
        self.insert(index, __object)

        # Serialize the object for Redis storage using a type adapter
        serialized_object = self._adapter.dump_python(
            [__object], mode="json", context={REDIS_DUMP_FLAG_NAME: True}
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
