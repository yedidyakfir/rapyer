from typing import TypeVar, Generic, get_args, Any

from rapyer.types.base import GenericRedisType, RedisType
from rapyer.types.utils import update_keys_in_pipeline

T = TypeVar("T")


class RedisDict(dict[str, T], GenericRedisType, Generic[T]):
    original_type = dict

    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[1] if args else Any

    async def load(self):
        # Get all items from Redis dict
        redis_items = await self.client.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = {}

        # Deserialize items using a type adapter
        adapter = self.inner_adapter()
        deserialized_items = {
            key: adapter.validate_python(value) for key, value in redis_items.items()
        }

        # Clear local dict and populate with Redis data
        super().clear()
        super().update(deserialized_items)

    async def aset_item(self, key, value):
        super().__setitem__(key, value)

        # Serialize the value for Redis storage using a type adapter
        adapter = self.inner_adapter()
        normalized_value = adapter.validate_python(value)
        serialized_value = adapter.dump_python(normalized_value, mode="json")
        return await self.client.json().set(
            self.redis_key, self.json_field_path(key), serialized_value
        )

    def __ior__(self, other):
        self.update(other)
        return self

    def __setitem__(self, key, value):
        new_val = self.create_new_value(key, value)
        new_val.base_model_link = self.base_model_link
        super().__setitem__(key, new_val)

    async def adel_item(self, key):
        super().__delitem__(key)

        return await self.client.json().delete(
            self.redis_key, self.json_field_path(key)
        )

    async def aupdate(self, **kwargs):
        self.update(**kwargs)

        # Serialize values using type adapter
        adapter = self.inner_adapter()
        redis_params = {
            self.json_field_path(key): adapter.dump_python(validated_v, mode="json")
            for key, v in kwargs.items()
            if (validated_v := adapter.validate_python(v))
        }

        # If I am in a pipeline, update keys in pipeline, otherwise execute pipeline
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
        # Key exists in Redis, pop from local dict (it should exist there too)
        super().pop(key, None)

        if result is None:
            # Key doesn't exist in Redis
            return default

        adapter = self.inner_adapter()
        return adapter.validate_json(result)

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
            # Pop the same key from the local dict
            super().pop(
                redis_key.decode() if isinstance(redis_key, bytes) else redis_key
            )
            adapter = self.inner_adapter()
            return adapter.validate_json(redis_value)
        else:
            # If Redis is empty but local dict has items, raise an error for consistency
            raise KeyError("popitem(): dictionary is empty")

    async def aclear(self):
        super().clear()
        # Clear Redis dict
        return await self.client.json().set(self.redis_key, self.json_path, {})

    def clone(self):
        return {
            k: v.clone() if isinstance(v, RedisType) else v for k, v in self.items()
        }
