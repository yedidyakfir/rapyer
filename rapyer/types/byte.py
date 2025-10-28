from rapyer.types.base import RedisType
from pydantic_core import core_schema


class RedisBytes(bytes, RedisType):
    original_type = bytes

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        return self._adapter.validate_python(redis_value)

    async def set(self, value: bytes):
        if not isinstance(value, bytes):
            raise TypeError("Value must be bytes")

        value = self._adapter.dump_python(value, mode="json")
        return await self.client.json().set(self.redis_key, self.json_path, value)

    def clone(self):
        return bytes(self)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.no_info_before_validator_function(
                cls._validate_pickle, handler(cls.original_type)
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize_pickle, return_schema=core_schema.str_schema()
            ),
        )

    @classmethod
    def _validate_pickle(cls, value):
        if isinstance(value, str):
            return cls.deserialize_unknown(value)
        return value

    @classmethod
    def _serialize_pickle(cls, value):
        return cls.serialize_unknown(bytes(value))
