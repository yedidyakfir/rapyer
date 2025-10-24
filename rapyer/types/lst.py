import json
from typing import TypeVar, Generic, Any

from rapyer.types.base import GenericRedisType, RedisType
from rapyer.types.utils import noop
from rapyer.utils import RedisTypeTransformer

T = TypeVar("T")


class RedisList(list[T], GenericRedisType, Generic[T]):
    original_type = list

    async def load(self):
        # Get all items from Redis list
        redis_items = await self.client.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = []

        # Clear local list and populate with Redis data
        super().clear()
        super().extend(redis_items)

    def sub_field_path(self, field_name: str):
        return f"{self.field_path}[{field_name}]"

    def create_new_type(self, key):
        inner_original_type = self.find_inner_type(self.original_type)
        type_transformer = RedisTypeTransformer(self.sub_field_path(key), self.Meta)
        new_type = type_transformer[inner_original_type]
        return new_type

    def create_new_value(self, key, value):
        new_type = self.create_new_type(key)
        if new_type is Any:
            return value
        return new_type(value)

    def __setitem__(self, key, value):
        new_val = self.create_new_value(key, value)
        new_val.base_model_link = self.base_model_link
        super().__setitem__(key, new_val)

    async def aappend(self, __object):
        key = len(self)
        new_val = self.create_new_value(key, __object)
        super().append(new_val)

        # Serialize the object for Redis storage
        return await self.client.json().arrappend(
            self.redis_key, self.json_path, __object
        )

    async def aextend(self, __iterable):
        items = list(__iterable)
        base_idx = len(self)
        redis_items = [
            self.create_new_value(base_idx + i, item) for i, item in enumerate(items)
        ]
        super().extend(redis_items)

        # Convert iterable to list and serialize items
        if items:
            return await self.client.json().arrappend(
                self.redis_key,
                self.json_path,
                *items,
            )

        return await noop()

    async def apop(self, index=-1):
        if self:
            super().pop(index)
        arrpop = await self.client.json().arrpop(self.redis_key, self.json_path, index)

        # Handle empty list case
        if arrpop is None or (isinstance(arrpop, list) and len(arrpop) == 0):
            return None

        # Handle case where arrpop returns [None] for empty list
        if arrpop[0] is None:
            return None

        result = json.loads(arrpop[0])

        adapter = self.inner_adapter()
        return adapter.validate_python(result)

    async def ainsert(self, index, __object):
        key = len(self)
        new_val = self.create_new_value(key, __object)
        super().insert(index, new_val)

        return await self.client.json().arrinsert(
            self.redis_key, self.json_path, index, __object
        )

    async def aclear(self):
        # Clear local list
        super().clear()

        # Clear Redis list
        return await self.client.json().set(self.redis_key, self.json_path, [])

    def clone(self):
        return [v.clone() if isinstance(v, RedisType) else v for v in self]
