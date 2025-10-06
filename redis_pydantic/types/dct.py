from typing import TypeVar, Generic, get_args

from redis_pydantic.types.base import GenericRedisType
from redis_pydantic.types.utils import update_keys_in_pipeline

T = TypeVar("T")


class RedisDict(dict[str, T], GenericRedisType, Generic[T]):
    def __init__(self, value=None, *args, **kwargs):
        # Extract value if passed as keyword argument
        GenericRedisType.__init__(self, **kwargs)
        super().__init__(value, *args)

    async def load(self):
        # Get all items from Redis dict
        redis_items = await self.client.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = {}

        # Deserialize items using inner_type
        deserialized_items = {}
        for key, value in redis_items.items():
            if self.inner_type is not None:
                # Use inner_type to deserialize the value
                deserialized_value = self.inner_type.deserialize_value(value)
                deserialized_items[key] = deserialized_value
            else:
                # No type conversion
                deserialized_items[key] = value

        # Clear local dict and populate with Redis data
        super().clear()
        super().update(deserialized_items)

    async def aset_item(self, key, value):
        super().__setitem__(key, value)

        # Serialize the value for Redis storage
        serialized_value = self.inner_type.serialize_value(value)
        return await self.client.json().set(
            self.redis_key, self.json_field_path(key), serialized_value
        )

    async def adel_item(self, key):
        super().__delitem__(key)

        return await self.client.json().delete(
            self.redis_key, self.json_field_path(key)
        )

    def _parse_redis_json_value(self, result):
        """Parse JSON-encoded value returned from Redis Lua scripts."""
        if isinstance(result, bytes):
            result = result.decode()
        if result.startswith("[") and result.endswith("]"):
            # Remove JSON array wrapping for single values
            result = result[1:-1]
            # Handle string values that were quoted
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
        return result

    async def aupdate(self, **kwargs):
        self.update(**kwargs)
        redis_params = {
            self.json_field_path(key): self.inner_type.serialize_value(v)
            for key, v in kwargs.items()
        }
        if self.pipeline:
            update_keys_in_pipeline(self.pipeline, self.redis_key, **redis_params)
            return

        async with self.redis.pipeline() as pipeline:
            update_keys_in_pipeline(pipeline, self.redis_key, **redis_params)
            await pipeline.execute()

    async def apop(self, key, default=None):
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
        result = await self.client.eval(
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

        # Deserialize the value using inner_type
        parsed_result = self._parse_redis_json_value(result)
        if self.inner_type is not None:
            return self.inner_type.deserialize_value(parsed_result)
        return parsed_result

    async def apopitem(self):
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
        result = await self.client.eval(
            popitem_script, 1, self.redis_key, self.json_path
        )

        if result is not None:
            redis_key, redis_value = result
            # Pop the same key from local dict
            super().pop(
                redis_key.decode() if isinstance(redis_key, bytes) else redis_key
            )
            parsed_value = self._parse_redis_json_value(redis_value)
            if self.inner_type is not None:
                parsed_value = self.inner_type.deserialize_value(parsed_value)
            return parsed_value
        else:
            # If Redis is empty but local dict has items, raise error for consistency
            raise KeyError("popitem(): dictionary is empty")

    async def aclear(self):
        # Clear local dict
        super().clear()

        # Clear Redis dict
        return await self.client.json().delete(self.redis_key, self.json_path)

    def clone(self):
        return dict.copy(self)

    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[1]

    def serialize_value(self, value):
        return {k: self.inner_type.serialize_value(v) for k, v in value.items()}

    def deserialize_value(self, value):
        return {k: self.inner_type.deserialize_value(v) for k, v in value.items()}
