from redis_pydantic.types.base import RedisType


class RedisDict(dict, RedisType):
    def __init__(self, *args, **kwargs):
        RedisType.__init__(self, **kwargs)
        super().__init__(*args)

    async def load(self):
        # Get all items from Redis dict
        redis_items = await self.pipeline.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = {}

        # Clear local dict and populate with Redis data
        super().clear()
        super().update(redis_items)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

        return self.pipeline.json().set(
            self.redis_key, f"{self.json_path}.{key}", str(value)
        )

    def __delitem__(self, key):
        super().__delitem__(key)

        return self.pipeline.json().delete(self.redis_key, f"{self.json_path}.{key}")

    def update(self, **kwargs):
        super().update(kwargs)
        redis_kwargs = {f"{self.json_path}.{k}": v for k, v in kwargs.items()}
        return self.pipeline.json().mset(
            [
                (self.redis_key, field_name, value)
                for field_name, value in redis_kwargs.items()
            ]
        )

    async def pop(self, key, default=None):
        # Redis Lua script for atomic get-and-delete operation
        pop_script = """
        local key = KEYS[1]
        local path = ARGV[1]
        local target_key = ARGV[2]
        
        -- Get the value from the JSON object
        local value = redis.call('JSON.GET', key, path .. '.' .. target_key)
        
        if value then
            -- Delete the key from the JSON object
            redis.call('JSON.DEL', key, path .. '.' .. target_key)
            return value
        else
            return nil
        end
        """

        # Execute the script atomically
        result = await self.pipeline.eval(
            pop_script, 1, self.redis_key, self.json_path, key
        )
        if result is None and default is not None:
            return default

        # Pop from local dict and return the local value
        super().pop(key, None)
        return result

    async def popitem(self):
        # Check if dict is empty first
        if len(self) == 0:
            raise KeyError("popitem(): dictionary is empty")

        # Get an arbitrary key from local dict
        local_key = next(iter(self))
        local_value = self[local_key]

        # Redis Lua script for atomic delete operation using the specific key
        popitem_script = """
        local key = KEYS[1]
        local path = ARGV[1]
        local target_key = ARGV[2]
        
        -- Delete the key from the JSON object
        local result = redis.call('JSON.DEL', key, path .. '.' .. target_key)
        return result
        """

        # Execute the script atomically to delete from Redis
        await self.pipeline.eval(
            popitem_script, 1, self.redis_key, self.json_path, local_key
        )

        # Pop the same key from local dict
        super().pop(local_key)
        return local_key, local_value

    def clear(self):
        # Clear local dict
        super().clear()

        # Clear Redis dict
        return self.pipeline.json().delete(self.redis_key, self.json_path)

    def clone(self):
        return dict.copy(self)
