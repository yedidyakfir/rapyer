from typing import TypeVar, Generic, get_args

from redis_pydantic.types.base import GenericRedisType

T = TypeVar('T')


class RedisDict(dict[str, T], GenericRedisType, Generic[T]):
    def __init__(self, *args, **kwargs):
        GenericRedisType.__init__(self, **kwargs)
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

    def _parse_redis_json_value(self, result):
        """Parse JSON-encoded value returned from Redis Lua scripts."""
        if isinstance(result, bytes):
            result = result.decode()
        if result.startswith('["') and result.endswith('"]'):
            # Remove JSON array wrapping for single values
            result = result[2:-2]
        return result

    def update(self, *args, **kwargs):
        # Handle different ways update can be called
        if args:
            other = args[0]
            if hasattr(other, "items"):
                for key, value in other.items():
                    self[key] = value
            else:
                for key, value in other:
                    self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    async def pop(self, key, default=None):
        # Redis Lua script for atomic get-and-delete operation
        pop_script = """
        local key = KEYS[1]
        local path = ARGV[1]
        local target_key = ARGV[2]
        
        -- Get the value from the JSON object
        local value = redis.call('JSON.GET', key, path .. '.' .. target_key)
        
        if value and value ~= '[]' and value ~= 'null' then
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

        if result is None:
            # Key doesn't exist in Redis
            if default is not None:
                return default
            else:
                raise KeyError(key)

        # Key exists in Redis, pop from local dict (it should exist there too)
        super().pop(
            key, None
        )  # Use None default to avoid KeyError if local is out of sync

        # Parse Redis value if it's JSON-encoded
        return self._parse_redis_json_value(result)

    async def popitem(self):
        # Redis Lua script for atomic get-arbitrary-key-and-delete operation
        popitem_script = """
        local key = KEYS[1]
        local path = ARGV[1]
        
        -- Get all the keys from the JSON object
        local keys_result = redis.call('JSON.OBJKEYS', key, path)
        
        if keys_result and type(keys_result) == 'table' and #keys_result > 0 then
            -- Get the first key from the result
            local keys = keys_result
            if type(keys[1]) == 'table' then
                keys = keys[1]  -- Sometimes Redis returns nested arrays
            end
            
            if #keys > 0 then
                local first_key = tostring(keys[1])
                -- Get the value for this key
                local value = redis.call('JSON.GET', key, path .. '.' .. first_key)
                
                if value then
                    -- Delete the key from the JSON object
                    redis.call('JSON.DEL', key, path .. '.' .. first_key)
                    return {first_key, value}
                end
            end
        end
        
        return nil
        """

        # Execute the script atomically
        result = await self.pipeline.eval(
            popitem_script, 1, self.redis_key, self.json_path
        )

        if result is not None:
            redis_key, redis_value = result
            # Pop the same key from local dict
            super().pop(
                redis_key.decode() if isinstance(redis_key, bytes) else redis_key
            )
            return self._parse_redis_json_value(redis_value)
        else:
            # If Redis is empty but local dict has items, raise error for consistency
            raise KeyError("popitem(): dictionary is empty")

    def clear(self):
        # Clear local dict
        super().clear()

        # Clear Redis dict
        return self.pipeline.json().delete(self.redis_key, self.json_path)

    def clone(self):
        return dict.copy(self)

    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[1]
