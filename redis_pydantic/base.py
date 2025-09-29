import asyncio
import json
import uuid
from typing import Any, get_origin, Self

import redis
from pydantic import BaseModel, Field

DEFAULT_CONNECTION = "redis://localhost:6379/0"


class RedisModel(BaseModel):
    pk: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Config:
        redis = redis.asyncio.from_url(DEFAULT_CONNECTION)

    @property
    def key(self):
        return f"{self.__class__.__name__}:{self.pk}"

    @classmethod
    async def get(cls, key: str) -> Self:
        redis_client = cls.Config.redis

        async def load_field(field_name: str) -> tuple[str, Any]:
            field_key = f"{key}/{field_name}"
            model_field_info = cls.model_fields[field_name]
            model_field_type = model_field_info.annotation

            if get_origin(model_field_type) is list or (
                isinstance(model_field_type, type)
                and issubclass(model_field_type, list)
            ):
                value = await redis_client.lrange(field_key, 0, -1)
                return field_name, value
            elif (
                get_origin(model_field_type) is dict
                or (
                    isinstance(model_field_type, type)
                    and issubclass(model_field_type, dict)
                )
                or (
                    isinstance(model_field_type, type)
                    and issubclass(model_field_type, BaseModel)
                )
            ):
                value = await redis_client.get(field_key)
                if value:
                    return field_name, (
                        value.decode() if isinstance(value, bytes) else value
                    )
                return field_name, None
            else:
                value = await redis_client.get(field_key)
                if value:
                    return field_name, (
                        value.decode() if isinstance(value, bytes) else value
                    )
                return field_name, None

        tasks = [load_field(field_name) for field_name in cls.model_fields]
        results = await asyncio.gather(*tasks)

        field_data = {}
        instance = cls.__new__(cls)

        for field_name, raw_value in results:
            if raw_value is not None:
                field_info = cls.model_fields[field_name]
                field_type = field_info.annotation

                if get_origin(field_type) is list:
                    field_data[field_name] = await instance._deserialize_field_value(
                        field_name, "list", raw_value
                    )
                elif (
                    get_origin(field_type) is dict
                    or (isinstance(field_type, type) and issubclass(field_type, dict))
                    or (
                        isinstance(field_type, type)
                        and issubclass(field_type, BaseModel)
                    )
                ):
                    field_data[field_name] = await instance._deserialize_field_value(
                        field_name, "json", raw_value
                    )
                else:
                    field_data[field_name] = await instance._deserialize_field_value(
                        field_name, "string", raw_value
                    )

        return cls(**field_data)

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
        return await self.update(**self.model_dump())
