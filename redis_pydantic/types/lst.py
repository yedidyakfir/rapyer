from redis_pydantic.types.base import RedisType
from redis_pydantic.types.utils import noop


class RedisList(list, RedisType):
    def __init__(self, *args, **kwargs):
        RedisType.__init__(self, **kwargs)
        super().__init__(*args)

    async def load(self):
        # Get all items from Redis list
        redis_items = await self.pipeline.json().get(self.redis_key, self.field_path)

        # Decode bytes to strings if needed
        decoded_items = [
            item.decode() if isinstance(item, bytes) else item for item in redis_items
        ]

        # Clear local list and populate with Redis data
        super().clear()
        super().extend(decoded_items)

    def append(self, __object):
        super().append(__object)

        return self.pipeline.json().arrappend(
            self.redis_key, self.json_path, str(__object)
        )

    def extend(self, __iterable):
        items = list(__iterable)
        super().extend(items)

        # Convert iterable to list and reverse for correct order with lpush
        if items:
            # Add all items to Redis in reverse order (lpush adds to front)
            return self.pipeline.json().arrappend(
                self.redis_key,
                self.json_path,
                *[str(item) for item in reversed(items)],
            )
        return noop()

    def pop(self, index=-1):
        super().pop(index)
        return self.pipeline.json().arrpop(self.redis_key, self.json_path, index)[0]

    def insert(self, index, __object):
        super().insert(index, __object)
        return self.pipeline.json().arrinsert(
            self.redis_key, self.json_path, index, str(__object)
        )

    def clear(self):
        # Clear local list
        super().clear()

        # Clear Redis list
        return self.pipeline.json().delete(self.redis_key, self.json_path)

    def clone(self):
        return list.copy(self)
