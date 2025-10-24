from typing import TypeVar, Generic

from rapyer.types.base import GenericRedisType, RedisType
from rapyer.types.utils import noop

T = TypeVar("T")


class RedisList(list[T], GenericRedisType, Generic[T]):
    original_type = list

    async def load(self) -> list[T]:
        # Get all items from Redis list
        redis_items = await self.client.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = []

        # Clear the local list and populate with Redis data using type adapter
        super().clear()
        if redis_items:
            adapter = self.inner_adapter()
            deserialized_items = [adapter.validate_python(item) for item in redis_items]
            super().extend(deserialized_items)
        return list(self)

    def __setitem__(self, key, value):
        new_val = self.create_new_value(key, value)
        new_val.base_model_link = self.base_model_link
        super().__setitem__(key, new_val)

    async def aappend(self, __object):
        key = len(self)
        new_val = self.create_new_value(key, __object)
        super().append(new_val)

        # Serialize the object for Redis storage using a type adapter
        adapter = self.inner_adapter()
        serialized_object = adapter.dump_python(new_val, mode="json")
        return await self.client.json().arrappend(
            self.redis_key, self.json_path, serialized_object
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
            adapter = self.inner_adapter()
            normalized_items = [adapter.validate_python(item) for item in items]
            serialized_items = [
                adapter.dump_python(item, mode="json") for item in normalized_items
            ]
            return await self.client.json().arrappend(
                self.redis_key,
                self.json_path,
                *serialized_items,
            )

        return await noop()

    async def apop(self, index=-1):
        if self:
            super().pop(index)
        arrpop = await self.client.json().arrpop(self.redis_key, self.json_path, index)

        # Handle empty list case
        if arrpop is None or (isinstance(arrpop, list) and len(arrpop) == 0):
            return None

        # Handle case where arrpop returns [None] for an empty list
        if arrpop[0] is None:
            return None

        adapter = self.inner_adapter()
        return adapter.validate_json(arrpop[0])

    async def ainsert(self, index, __object):
        key = len(self)
        new_val = self.create_new_value(key, __object)
        super().insert(index, new_val)

        # Serialize the object for Redis storage using a type adapter
        adapter = self.inner_adapter()
        normalized_object = adapter.validate_python(__object)
        serialized_object = adapter.dump_python(normalized_object, mode="json")
        return await self.client.json().arrinsert(
            self.redis_key, self.json_path, index, serialized_object
        )

    async def aclear(self):
        # Clear local list
        super().clear()

        # Clear Redis list
        return await self.client.json().set(self.redis_key, self.json_path, [])

    def clone(self):
        return [v.clone() if isinstance(v, RedisType) else v for v in self]
