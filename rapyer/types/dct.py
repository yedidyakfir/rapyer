from typing import TypeVar, Generic, get_args, Any

from rapyer.config import RedisFieldConfig
from rapyer.types.base import GenericRedisType, RedisSerializer, RedisType
from rapyer.types.utils import update_keys_in_pipeline

T = TypeVar("T")


class DictSerializer(RedisSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inner_serializer = self._create_inner_serializer()

    def _create_inner_serializer(self):
        args = get_args(self.full_type)
        if len(args) >= 2:
            value_type = args[1]
            # dict[key_type, value_type] - we care about value_type
            return self.serializer_creator(value_type)
        return None

    def serialize_value(self, value):
        if self.inner_serializer:
            return {
                k: self.inner_serializer.serialize_value(v) for k, v in value.items()
            }
        return dict(value)

    def deserialize_value(self, value):
        if value is None:
            return None
        if self.inner_serializer:
            return {
                k: self.inner_serializer.deserialize_value(v) for k, v in value.items()
            }
        return dict(value)


class RedisDict(dict[str, T], GenericRedisType, Generic[T]):
    def __init__(self, value=None, *args, **kwargs):
        # Extract value if passed as keyword argument
        GenericRedisType.__init__(self, **kwargs)
        super().__init__(value, *args)

    @classmethod
    def find_inner_type(cls, type_):
        args = get_args(type_)
        return args[1] if args else Any

    async def load(self):
        # Get all items from Redis dict
        redis_items = await self.client.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = {}

        # Deserialize items using serializer
        deserialized_items = {}
        for key, value in redis_items.items():
            if self.serializer is not None:
                # Use serializer to deserialize the value
                deserialized_value = self.serializer.deserialize_value(value)
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
        serialized_value = (
            self.serializer.serialize_value(value) if self.serializer else value
        )
        return await self.client.json().set(
            self.redis_key, self.json_field_path(key), serialized_value
        )

    def __ior__(self, other):
        self.update(other)
        return self

    def __setitem__(self, key, value):
        redis_type, kwargs = self.inner_type
        field_path = f"{self.field_path}.{key}"
        new_val = self.inst_init(
            redis_type,
            value,
            self.redis_key,
            **kwargs,
            redis=self.redis,
            field_path=field_path,
            _field_config_override=RedisFieldConfig(field_path=field_path),
        )
        return super().__setitem__(key, new_val)

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
            self.json_field_path(key): (
                self.serializer.serialize_value(v) if self.serializer else v
            )
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
        # Key exists in Redis, pop from local dict (it should exist there too)
        super().pop(key, None)

        if result is None:
            # Key doesn't exist in Redis
            return default

        # Deserialize the value using serializer
        parsed_result = self._parse_redis_json_value(result)
        if self.serializer is not None:
            return self.serializer.deserialize_value(parsed_result)
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
            if self.serializer is not None:
                parsed_value = self.serializer.deserialize_value(parsed_value)
            return parsed_value
        else:
            # If Redis is empty but local dict has items, raise error for consistency
            raise KeyError("popitem(): dictionary is empty")

    async def aclear(self):
        # Clear local dict
        super().clear()

        # Clear Redis dict
        return await self.client.json().set(self.redis_key, self.json_path, {})

    def clone(self):
        return {
            k: v.clone() if isinstance(v, RedisType) else v for k, v in self.items()
        }

    def serialize_value(self, value):
        return {k: self.serializer.serialize_value(v) for k, v in value.items()}

    def deserialize_value(self, value):
        return {k: self.serializer.deserialize_value(v) for k, v in value.items()}
