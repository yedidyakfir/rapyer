from typing import TypeVar, Generic

from redis_pydantic.types.base import GenericRedisType
from redis_pydantic.types.utils import noop

T = TypeVar("T")


class RedisList(list[T], GenericRedisType, Generic[T]):
    def __init__(self, *args, **kwargs):
        GenericRedisType.__init__(self, **kwargs)
        super().__init__(*args)

    async def load(self):
        # Get all items from Redis list
        redis_items = await self.client.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = []

        # Deserialize items using inner_type
        deserialized_items = []
        for item in redis_items:
            if self.inner_type is not None:
                # If inner_type is a tuple (Redis type, resolved inner type), use the resolved type
                deserialized_item = self.inner_type.deserialize_value(item)
                deserialized_items.append(deserialized_item)
            else:
                # Fallback to decode bytes if no inner_type
                decoded_item = item.decode() if isinstance(item, bytes) else item
                deserialized_items.append(decoded_item)

        # Clear local list and populate with Redis data
        super().clear()
        super().extend(deserialized_items)

    async def aappend(self, __object):
        super().append(__object)

        # Serialize the object for Redis storage
        serialized_object = self.inner_type.serialize_value(__object)
        return await self.client.json().arrappend(
            self.redis_key, self.json_path, serialized_object
        )

    async def aextend(self, __iterable):
        items = list(__iterable)
        super().extend(items)

        # Convert iterable to list and serialize items
        if items:
            # Serialize all items for Redis storage
            serialized_items = [self.inner_type.serialize_value(item) for item in items]

            return await self.client.json().arrappend(
                self.redis_key,
                self.json_path,
                *serialized_items,
            )

        return await noop()

    async def apop(self, index=-1):
        super().pop(index)
        arrpop = await self.client.json().arrpop(self.redis_key, self.json_path, index)
        return self.inner_type.deserialize_value(arrpop[0])

    async def ainsert(self, index, __object):
        super().insert(index, __object)

        # Serialize the object for Redis storage
        serialized_object = self.inner_type.serialize_value(__object)

        return await self.client.json().arrinsert(
            self.redis_key, self.json_path, index, serialized_object
        )

    async def aclear(self):
        # Clear local list
        super().clear()

        # Clear Redis list
        return await self.client.json().delete(self.redis_key, self.json_path)

    def clone(self):
        return list.copy(self)

    def serialize_value(self, value):
        return [self.inner_type.serialize_value(v) for v in value]

    def deserialize_value(self, value):
        return [self.inner_type.deserialize_value(v) for v in value]
