from typing import TypeVar, Generic
from typing import get_args

from redis_pydantic.types.base import GenericRedisType, RedisSerializer
from redis_pydantic.types.utils import noop

T = TypeVar("T")


class ListSerializer(RedisSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inner_serializer = self._create_inner_serializer()

    def _create_inner_serializer(self):
        args = get_args(self.full_type)
        if args:
            inner_type = args[0]
            return self.serializer_creator(inner_type)
        return None

    def serialize_value(self, value):
        if value is None:
            return None
        if self.inner_serializer:
            return [self.inner_serializer.serialize_value(v) for v in value]
        return list(value)

    def deserialize_value(self, value):
        if value is None:
            return None
        if self.inner_serializer:
            return [self.inner_serializer.deserialize_value(v) for v in value]
        return list(value)


class RedisList(list[T], GenericRedisType, Generic[T]):
    def __init__(self, value, *args, **kwargs):
        super().__init__(value)
        GenericRedisType.__init__(self, *args, **kwargs)

    async def load(self):
        # Get all items from Redis list
        redis_items = await self.client.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = []

        # Deserialize items using serializer
        deserialized_items = []
        for item in redis_items:
            if self.serializer is not None:
                deserialized_item = self.serializer.deserialize_value(item)
                deserialized_items.append(deserialized_item)
            else:
                # Fallback to decode bytes if no serializer
                decoded_item = item.decode() if isinstance(item, bytes) else item
                deserialized_items.append(decoded_item)

        # Clear local list and populate with Redis data
        super().clear()
        super().extend(deserialized_items)

    async def aappend(self, __object):
        super().append(__object)

        # Serialize the object for Redis storage
        serialized_object = (
            self.serializer.serialize_value(__object) if self.serializer else __object
        )
        return await self.client.json().arrappend(
            self.redis_key, self.json_path, serialized_object
        )

    async def aextend(self, __iterable):
        items = list(__iterable)
        super().extend(items)

        # Convert iterable to list and serialize items
        if items:
            # Serialize all items for Redis storage
            serialized_items = [
                self.serializer.serialize_value(item) if self.serializer else item
                for item in items
            ]

            return await self.client.json().arrappend(
                self.redis_key,
                self.json_path,
                *serialized_items,
            )

        return await noop()

    async def apop(self, index=-1):
        super().pop(index)
        arrpop = await self.client.json().arrpop(self.redis_key, self.json_path, index)
        return (
            self.serializer.deserialize_value(arrpop[0])
            if self.serializer
            else arrpop[0]
        )

    async def ainsert(self, index, __object):
        super().insert(index, __object)

        # Serialize the object for Redis storage
        serialized_object = (
            self.serializer.serialize_value(__object) if self.serializer else __object
        )

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
        return [self.serializer.serialize_value(v) for v in value]

    def deserialize_value(self, value):
        return [self.serializer.deserialize_value(v) for v in value]
