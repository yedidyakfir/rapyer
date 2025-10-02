import asyncio
import json
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, get_origin, get_args, Self, Union, Annotated

import redis
from pydantic import BaseModel, Field, PrivateAttr
from redis.asyncio.client import Pipeline

from redis_pydantic.types import ALL_TYPES

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


class RedisFieldDescriptor:
    """Descriptor that creates Redis type instances with proper parameters."""

    def __init__(self, redis_type_class, field_name, default_value=None):
        self.redis_type_class = redis_type_class
        self.field_name = field_name
        self.default_value = default_value
        self.private_name = f"_redis_{field_name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        # Get or create the Redis type instance
        if not hasattr(obj, self.private_name):
            # Prepare initial value
            initial_value = []
            if self.default_value is not None:
                if callable(self.default_value):
                    initial_value = self.default_value()
                else:
                    initial_value = self.default_value

            # Create instance with current parameters and initial value
            redis_instance = self.redis_type_class(
                initial_value,
                redis_key=obj.key,
                field_path=self.field_name,
                redis=obj.Meta.redis,
            )
            setattr(obj, self.private_name, redis_instance)

        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        # Create new Redis type instance with the value
        initial_value = value if value is not None else []
        redis_instance = self.redis_type_class(
            initial_value,
            redis_key=obj.key,
            field_path=self.field_name,
            redis=obj.Meta.redis,
        )
        setattr(obj, self.private_name, redis_instance)

    def __delete__(self, obj):
        if hasattr(obj, self.private_name):
            delattr(obj, self.private_name)


class BaseRedisModel(BaseModel):
    _pk: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))

    class Meta:
        redis = redis.asyncio.from_url(DEFAULT_CONNECTION)
        redis_type: dict[str, type] = ALL_TYPES

    @property
    def pk(self):
        return self._pk

    @pk.setter
    def pk(self, value: str):
        self._pk = value
        self._update_redis_field_parameters()

    @property
    def key(self):
        return f"{self.__class__.__name__}:{self.pk}"

    def _update_redis_field_parameters(self):
        """Update Redis field parameters when key or redis connection changes."""
        for field_name in getattr(self.__class__, "_redis_field_mapping", {}):
            if hasattr(self, field_name):
                redis_instance = getattr(self, field_name)
                if hasattr(redis_instance, "redis_key") and hasattr(
                    redis_instance, "redis"
                ):
                    redis_instance.redis_key = self.key
                    redis_instance.redis = self.Meta.redis

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Store Redis field mappings for later use
        cls._redis_field_mapping = {}

        # Replace field types with Redis types and create descriptors
        for field_name, field_type in cls.__annotations__.items():
            actual_type = get_actual_type(field_type)

            # Handle generic types like list[str] by checking the origin
            origin_type = get_origin(actual_type) or actual_type

            # Check if this type should be replaced with a Redis type
            if origin_type in cls.Meta.redis_type:
                redis_type_class = cls.Meta.redis_type[origin_type]
                cls._redis_field_mapping[field_name] = redis_type_class

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize Redis fields after Pydantic initialization
        for field_name, redis_type_class in getattr(
            self.__class__, "_redis_field_mapping", {}
        ).items():
            # Get the current value (from Pydantic initialization)
            current_value = getattr(self, field_name, [])

            # Create Redis type instance
            redis_instance = redis_type_class(
                current_value,
                redis_key=self.key,
                field_path=field_name,
                redis=self.Meta.redis,
            )

            # Set it directly on the instance
            object.__setattr__(self, field_name, redis_instance)

    async def save(self) -> Self:
        model_dump = self.model_dump(exclude=["_pk"])
        await self.Meta.redis.json().set(self.key, "$", model_dump)
        return self


class RedisModel(BaseModel):
    pk: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Meta:
        redis = redis.asyncio.from_url(DEFAULT_CONNECTION)

    @property
    def key(self):
        return f"{self.__class__.__name__}:{self.pk}"

    async def load(self, *field_names: str) -> Self:
        fields = await self.load_fields(self.key, *field_names)
        # Update only the selected fields on this instance
        for name, value in fields.items():
            setattr(self, name, value)
        return self

    @classmethod
    async def load_fields(cls, key: str, *field_names: str) -> dict[str, Any]:
        """Load only selected fields from Redis for a model instance."""
        redis_client = cls.Meta.redis

        # Validate field names
        invalid_fields = [name for name in field_names if name not in cls.model_fields]
        if invalid_fields:
            raise ValueError(f"Invalid field names: {invalid_fields}")

        tasks = [
            cls.load_field(key, field_name, redis_client) for field_name in field_names
        ]
        results = await asyncio.gather(*tasks)

        field_data = {}
        temp_instance = cls.__new__(cls)

        for field_name, raw_value in results:
            if raw_value is not None:
                field_info = cls.model_fields[field_name]
                field_type = field_info.annotation
                actual_type = get_actual_type(field_type)

                if get_origin(actual_type) is list:
                    field_data[field_name] = (
                        temp_instance._deserialize_list_for_load_fields(
                            field_name, raw_value
                        )
                    )
                elif (
                    get_origin(actual_type) is dict
                    or (isinstance(actual_type, type) and issubclass(actual_type, dict))
                    or (
                        isinstance(actual_type, type)
                        and issubclass(actual_type, BaseModel)
                    )
                ):
                    field_data[field_name] = (
                        await temp_instance._deserialize_field_value(
                            field_name, "json", raw_value
                        )
                    )
                elif actual_type == bytes:
                    field_data[field_name] = (
                        await temp_instance._deserialize_field_value(
                            field_name, "bytes", raw_value
                        )
                    )
                else:
                    field_data[field_name] = (
                        await temp_instance._deserialize_field_value(
                            field_name, "string", raw_value
                        )
                    )

        return field_data

    @classmethod
    async def load_field(cls, key, field_name: str, redis_client) -> tuple[str, Any]:
        field_key = f"{key}/{field_name}"
        model_field_info = cls.model_fields[field_name]
        model_field_type = model_field_info.annotation
        model_actual_type = get_actual_type(model_field_type)

        if get_origin(model_actual_type) is list or (
            isinstance(model_actual_type, type) and issubclass(model_actual_type, list)
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

    @classmethod
    async def get(cls, key: str) -> Self:
        redis_client = cls.Meta.redis

        tasks = [
            cls.load_field(key, field_name, redis_client)
            for field_name in cls.model_fields
        ]
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
        elif isinstance(value, Enum):
            return "string", value.value
        elif isinstance(value, (str, int, float, bool)):
            return "string", str(value)
        elif value is None:
            return "string", ""
        else:
            return "json", json.dumps(value)

    def _deserialize_list_for_load_fields(self, field_name: str, value: Any) -> Any:
        """Special deserialization for lists in load_fields to handle type conversion properly."""
        field_info = self.model_fields[field_name]
        field_type = field_info.annotation
        actual_type = get_actual_type(field_type)

        if not value:
            return value

        list_args = get_args(actual_type)
        if list_args:
            item_type = list_args[0]
            actual_item_type = get_actual_type(item_type)

            # Handle Annotated types
            from typing import _AnnotatedAlias

            if (
                isinstance(item_type, _AnnotatedAlias)
                or get_origin(item_type) is Annotated
            ):
                # For Annotated[int, ...] we want the actual int type
                actual_item_type = get_args(item_type)[0]

            converted_items = []
            for item in value:
                # Decode bytes to string first if needed
                if isinstance(item, bytes):
                    item = item.decode()

                # Convert to the appropriate type
                if actual_item_type == int:
                    converted_items.append(int(item))
                elif actual_item_type == float:
                    converted_items.append(float(item))
                elif actual_item_type == bool:
                    converted_items.append(
                        item.lower() == "true" if isinstance(item, str) else bool(item)
                    )
                elif actual_item_type == datetime:
                    converted_items.append(datetime.fromisoformat(item))
                elif actual_item_type == Decimal:
                    converted_items.append(Decimal(item))
                else:
                    converted_items.append(item)

            return converted_items
        else:
            # No type info, decode bytes to strings
            return [
                item.decode() if isinstance(item, bytes) else item for item in value
            ]

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
            elif isinstance(actual_type, type) and issubclass(actual_type, Enum):
                return actual_type(value)
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
        cls, redis_id: str, ignore_if_deleted: bool = True, **kwargs
    ) -> bool:
        redis_client = cls.Meta.redis
        cls.validate_fields(**kwargs)

        async with redis_client.pipeline(transaction=True) as pipe:
            for field_name, value in kwargs.items():
                field_key = create_field_key(redis_id, field_name)
                pipe = cls._update_field_in_redis(
                    pipe, field_key, value, xx=ignore_if_deleted
                )

            await pipe.execute()
        return True

    async def update(self, **kwargs) -> bool:
        for field_name, value in kwargs.items():
            if field_name in self.model_fields:
                setattr(self, field_name, value)

        return await self.update_from_id(self.key, **kwargs)

    async def save(self) -> Self:
        # Get only the actual model fields, excluding computed fields
        dump_data = {
            k: v for k, v in self.model_dump().items() if k in self.model_fields
        }
        await self.update_from_id(self.key, ignore_if_deleted=False, **dump_data)
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

    @classmethod
    async def pop_from_key(cls, key: str, field_name: str) -> Any:
        redis_client = cls.Meta.redis
        field_key = create_field_key(key, field_name)

        if field_name not in cls.model_fields:
            raise ValueError(f"Field {field_name} not found in {cls.__name__}")

        field_info = cls.model_fields[field_name]
        field_type = field_info.annotation
        actual_type = get_actual_type(field_type)

        if get_origin(actual_type) is list or (
            isinstance(actual_type, type) and issubclass(actual_type, list)
        ):
            value = await redis_client.lpop(field_key)
            if value is None:
                return None

            # Handle type conversion for list items
            list_args = get_args(actual_type)
            if list_args:
                item_type = list_args[0]
                actual_item_type = get_actual_type(item_type)

                # Handle Annotated types
                from typing import _AnnotatedAlias

                if (
                    isinstance(item_type, _AnnotatedAlias)
                    or get_origin(item_type) is Annotated
                ):
                    actual_item_type = get_args(item_type)[0]

                # Decode bytes to string first if needed
                if isinstance(value, bytes):
                    value = value.decode()

                # Convert to the appropriate type
                if actual_item_type == int:
                    return int(value)
                elif actual_item_type == float:
                    return float(value)
                elif actual_item_type == bool:
                    return (
                        value.lower() == "true"
                        if isinstance(value, str)
                        else bool(value)
                    )
                elif actual_item_type == datetime:
                    return datetime.fromisoformat(value)
                elif actual_item_type == Decimal:
                    return Decimal(value)
                else:
                    return value
            else:
                # No type info, decode bytes to string
                return value.decode() if isinstance(value, bytes) else value
        else:
            raise ValueError(f"Field {field_name} is not a list type")

    async def pop(self, field_name: str) -> Any:
        popped_value = await self.pop_from_key(self.key, field_name)

        # Update the local object by removing the popped value
        if hasattr(self, field_name):
            current_list = getattr(self, field_name, [])
            if current_list and len(current_list) > 0:
                # Remove the first element (LPOP removes from the left/head)
                current_list.pop(0)
                setattr(self, field_name, current_list)

        return popped_value


# TODO - return if update was successful
# TODO - get the values after incrby and after lpush to store it
# TODO - imporve get
# TODO - move to metaclass
# TODO - create wrapper for each supported type
# TODO - add flag to put multiple fields in one key
# TODO - allow foreign keys
# TODO - how to handle list of models?
# TODO - create a lock as context manager, with updated self - also it should accept different actions
