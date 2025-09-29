import asyncio
import json
import uuid
from typing import Any, get_origin, Self

import redis
from pydantic import BaseModel, Field
from redis.asyncio.client import Pipeline

DEFAULT_CONNECTION = "redis://localhost:6379/0"


def create_field_key(key: str, field_name: str) -> str:
    return f"{key}/{field_name}"


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
    def _update_field_in_redis(
        cls, pipe: Pipeline, key: str, value: Any, xx: bool = False
    ) -> Pipeline:
        redis_type, serialized_value = cls._serialize_field_value(value)

        if redis_type == "list":
            pipe.delete(key)
            if serialized_value:
                pipe.lpush(key, *reversed(serialized_value))
        elif redis_type == "json":
            pipe.set(key, serialized_value, xx=xx)
        elif redis_type == "string":
            pipe.set(key, serialized_value, xx=xx)
        return pipe

    @classmethod
    def validate_fields(cls, **kwargs):
        for field_name, value in kwargs.items():
            if field_name not in cls.model_fields:
                raise ValueError(f"Field {field_name} not found in {cls.__name__}")

    @classmethod
    async def update_from_id(
        cls, redis_id: str, ignore_if_deleted: bool = False, **kwargs
    ):
        redis_client = cls.Config.redis
        cls.validate_fields(**kwargs)

        async with redis_client.pipeline(transaction=True) as pipe:
            for field_name, value in kwargs.items():

                field_key = create_field_key(redis_id, field_name)
                pipe = cls._update_field_in_redis(
                    pipe, field_key, value, xx=ignore_if_deleted
                )

            await pipe.execute()

    async def update(self, **kwargs) -> Self:
        for field_name, value in kwargs.items():
            if field_name in self.model_fields:
                setattr(self, field_name, value)

        await self.update_from_id(self.key, ignore_if_deleted=True, **kwargs)
        return self

    async def save(self) -> Self:
        await self.update_from_id(self.key, **self.model_dump())
        return self

    @classmethod
    async def delete_from_key(cls, key: str):
        redis_client = cls.Config.redis

        async with redis_client.pipeline(transaction=True) as pipe:
            for field_name in cls.model_fields:
                field_key = create_field_key(key, field_name)
                pipe.delete(field_key)

            await pipe.execute()

    async def delete(self):
        await self.delete_from_key(self.key)

    @classmethod
    async def append_to_list_from_key(cls, key: str, list_name: str, value: Any):
        redis_client = cls.Config.redis
        field_key = create_field_key(key, list_name)

        await redis_client.lpush(field_key, value)

    async def append_to_list(self, list_name: str, value: Any):
        await self.append_to_list_from_key(self.key, list_name, value)
        
        if hasattr(self, list_name):
            current_list = getattr(self, list_name, [])
            if current_list is None:
                current_list = []
            current_list.insert(0, value)
            setattr(self, list_name, current_list)

    @classmethod
    async def increase_counter_from_key(
        cls, key: str, counter_name: str, value: int = 1
    ):
        redis_client = cls.Config.redis
        field_key = create_field_key(key, counter_name)

        await redis_client.incrby(field_key, value)

    async def increase_counter(self, counter_name: str, value: int = 1):
        await self.increase_counter_from_key(self.key, counter_name, value)
        
        if hasattr(self, counter_name):
            current_value = getattr(self, counter_name, 0)
            if current_value is None:
                current_value = 0
            new_value = int(current_value) + value
            setattr(self, counter_name, new_value)
