import asyncio
import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, get_origin, get_args, Self, Union

import redis
from pydantic import BaseModel, Field
from redis.asyncio.client import Pipeline

DEFAULT_CONNECTION = "redis://localhost:6379/0"


def create_field_key(key: str, field_name: str) -> str:
    return f"{key}/{field_name}"


def get_actual_type(annotation: Any) -> Any:
    """Extract the actual type from Optional/Union types."""
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        # Handle Optional[T] which is Union[T, None]
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
        return annotation  # Return as-is for complex Union types
    return annotation


class RedisModel(BaseModel):
    pk: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Meta:
        redis = redis.asyncio.from_url(DEFAULT_CONNECTION)

    @property
    def key(self):
        return f"{self.__class__.__name__}:{self.pk}"

    @classmethod
    async def get(cls, key: str) -> Self:
        redis_client = cls.Meta.redis

        async def load_field(field_name: str) -> tuple[str, Any]:
            field_key = f"{key}/{field_name}"
            model_field_info = cls.model_fields[field_name]
            model_field_type = model_field_info.annotation
            model_actual_type = get_actual_type(model_field_type)

            if get_origin(model_actual_type) is list or (
                isinstance(model_actual_type, type)
                and issubclass(model_actual_type, list)
            ):
                value = await redis_client.lrange(field_key, 0, -1)
                return field_name, value
            elif (
                get_origin(model_actual_type) is dict
                or (
                    isinstance(model_actual_type, type)
                    and issubclass(model_actual_type, dict)
                )
                or (
                    isinstance(model_actual_type, type)
                    and issubclass(model_actual_type, BaseModel)
                )
            ):
                value = await redis_client.get(field_key)
                if value:
                    return field_name, (
                        value.decode() if isinstance(value, bytes) else value
                    )
                return field_name, None
            elif model_actual_type == bytes:
                value = await redis_client.get(field_key)
                return field_name, value
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
                actual_type = get_actual_type(field_type)

                if get_origin(actual_type) is list:
                    field_data[field_name] = await instance._deserialize_field_value(
                        field_name, "list", raw_value
                    )
                elif (
                    get_origin(actual_type) is dict
                    or (isinstance(actual_type, type) and issubclass(actual_type, dict))
                    or (
                        isinstance(actual_type, type)
                        and issubclass(actual_type, BaseModel)
                    )
                ):
                    field_data[field_name] = await instance._deserialize_field_value(
                        field_name, "json", raw_value
                    )
                elif actual_type == bytes:
                    field_data[field_name] = await instance._deserialize_field_value(
                        field_name, "bytes", raw_value
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
        elif isinstance(value, datetime):
            return "string", value.isoformat()
        elif isinstance(value, bytes):
            return "bytes", value
        elif isinstance(value, Decimal):
            return "string", str(value)
        elif isinstance(value, (str, int, float, bool)):
            return "string", str(value)
        elif value is None:
            return "string", ""
        else:
            return "json", json.dumps(value)

    async def _deserialize_field_value(
        self, field_name: str, redis_type: str, value: Any
    ) -> Any:
        field_info = self.model_fields[field_name]
        field_type = field_info.annotation
        actual_type = get_actual_type(field_type)

        if redis_type == "json":
            if (
                get_origin(actual_type) is dict
                or isinstance(actual_type, type)
                and issubclass(actual_type, dict)
            ):
                return json.loads(value)
            elif isinstance(actual_type, type) and issubclass(actual_type, BaseModel):
                return actual_type.model_validate_json(value)
            else:
                return json.loads(value)
        elif redis_type == "list":
            return value
        elif redis_type == "bytes":
            # Check if the field is optional and value is empty
            if value == b"" and get_origin(field_type) is Union:
                return None
            return value
        elif redis_type == "string":
            if not value and get_origin(field_type) is Union:
                return None
            elif actual_type == int:
                return int(value)
            elif actual_type == float:
                return float(value)
            elif actual_type == bool:
                return value.lower() == "true"
            elif actual_type == datetime:
                return datetime.fromisoformat(value)
            elif actual_type == Decimal:
                return Decimal(value)
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
        elif redis_type == "bytes":
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
        redis_client = cls.Meta.redis
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
        # Get only the actual model fields, excluding computed fields
        dump_data = {k: v for k, v in self.model_dump().items() if k in self.model_fields}
        await self.update_from_id(self.key, **dump_data)
        return self

    @classmethod
    async def delete_from_key(cls, key: str):
        redis_client = cls.Meta.redis

        async with redis_client.pipeline(transaction=True) as pipe:
            for field_name in cls.model_fields:
                field_key = create_field_key(key, field_name)
                pipe.delete(field_key)

            await pipe.execute()

    async def delete(self):
        await self.delete_from_key(self.key)

    @classmethod
    async def append_to_list_from_key(cls, key: str, list_name: str, value: Any):
        redis_client = cls.Meta.redis
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
        redis_client = cls.Meta.redis
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


# TODO - return if update was successful
# TODO - get the values after incrby and after lpush to store it
# TODO - imporve get
# TODO - move to metaclass
# TODO - create wrapper for each supported type
# TODO - add flag to put multiple fields in one key
# TODO - allow foreign keys
