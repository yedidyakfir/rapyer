import json
import uuid
from typing import Any, get_origin, Self

import redis
from pydantic import BaseModel, Field

from redis_pydantic.config import settings


class RedisModel(BaseModel):
    pk: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Config:
        redis = redis.asyncio.from_url(settings.redis.url)

    @property
    def key(self):
        return f"{self.__class__.__name__}:{self.pk}"

    @classmethod
    def _serialize_field_value(cls, value: Any) -> tuple[str, Any]:
        if isinstance(value, BaseModel):
            return "json", value.model_dump_json()
        elif isinstance(value, dict):
            return "json", json.dumps(value)
        elif isinstance(value, list):
            return "list", value
        elif isinstance(value, (str, int, float, bool)):
            return "string", str(value)
        else:
            raise ValueError(f"Unsupported field type for {type(value)}")

    async def _deserialize_field_value(
        self, field_name: str, redis_type: str, value: Any
    ) -> Any:
        field_info = self.model_fields[field_name]
        field_type = field_info.annotation

        if redis_type == "json":
            if (
                get_origin(field_type) is dict
                or isinstance(field_type, type)
                and issubclass(field_type, dict)
            ):
                return json.loads(value)
            elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
                return field_type.model_validate_json(value)
            else:
                return json.loads(value)
        elif redis_type == "list":
            return value
        elif redis_type == "string":
            if field_type == int:
                return int(value)
            elif field_type == float:
                return float(value)
            elif field_type == bool:
                return value.lower() == "true"
            else:
                return value
        else:
            return value

    @classmethod
    def _update_field_in_redis(cls, pipe: Any, key: str, value: Any):
        redis_type, serialized_value = cls._serialize_field_value(value)

        if redis_type == "list":
            pipe.delete(key)
            if serialized_value:
                pipe.lpush(key, *serialized_value)
        elif redis_type == "json":
            pipe.set(key, serialized_value)
        elif redis_type == "string":
            pipe.set(key, serialized_value)
        return pipe

    @classmethod
    def validate_fields(cls, **kwargs):
        for field_name, value in kwargs.items():
            if field_name not in cls.model_fields:
                raise ValueError(f"Field {field_name} not found in {cls.__name__}")

    @classmethod
    async def update_from_id(cls, redis_id: str, **kwargs) -> None:
        redis_client = cls.Config.redis
        cls.validate_fields(**kwargs)

        async with redis_client.pipeline(transaction=True) as pipe:
            for field_name, value in kwargs.items():

                field_key = f"{redis_id}/{field_name}"
                pipe = cls._update_field_in_redis(pipe, field_key, value)

            await pipe.execute()

    async def update(self, **kwargs) -> Self:
        for field_name, value in kwargs.items():
            if field_name in self.model_fields:
                setattr(self, field_name, value)

        await self.update_from_id(self.key, **kwargs)
        return self

    async def save(self) -> Self:
        return self.update(**self.model_dump())
