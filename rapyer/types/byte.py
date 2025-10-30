from pydantic_core.core_schema import ValidationInfo, SerializationInfo

from rapyer.types.base import RedisType, REDIS_DUMP_FLAG_NAME
from pydantic_core import core_schema


class RedisBytes(bytes, RedisType):
    original_type = bytes

    async def load(self):
        redis_value = await self.client.json().get(self.key, self.field_path)
        return self._adapter.validate_python(
            redis_value, context={REDIS_DUMP_FLAG_NAME: True}
        )


    def clone(self):
        return bytes(self)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.with_info_before_validator_function(
                cls._validate_pickle, handler(cls.original_type)
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize_pickle,
                return_schema=core_schema.str_schema(),
                info_arg=True,
            ),
        )

    @classmethod
    def _validate_pickle(cls, value, info: ValidationInfo):
        ctx = info.context or {}
        is_redis_data = ctx.get(REDIS_DUMP_FLAG_NAME)

        if isinstance(value, str) and is_redis_data:
            return cls.deserialize_unknown(value)
        return value

    @classmethod
    def _serialize_pickle(cls, value, info: SerializationInfo):
        ctx = info.context or {}
        is_redis_data = ctx.get(REDIS_DUMP_FLAG_NAME)

        value = bytes(value)
        if is_redis_data:
            return cls.serialize_unknown(value)
        return value
