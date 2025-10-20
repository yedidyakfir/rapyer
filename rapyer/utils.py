import asyncio
import contextlib
import inspect
import uuid
from datetime import timedelta
from typing import get_origin, ClassVar, Union, get_args, Any, Annotated

from pydantic.fields import ModelPrivateAttr
from redis.asyncio import Redis

from rapyer.config import RedisConfig
from rapyer.types.base import BaseRedisType


@contextlib.asynccontextmanager
async def acquire_lock(
    redis: Redis, key: str, lock_timeout: timedelta | int = 10, sleep_time: int = 0.1
):
    lock_key = f"{key}:lock"
    lock_token = str(uuid.uuid4())
    while not await redis.set(lock_key, lock_token, nx=True, ex=lock_timeout):
        await asyncio.sleep(sleep_time)
    try:
        yield
    finally:
        await redis.delete(lock_key)


def get_public_instance_annotations(cls):
    all_annotations = {}

    for parent in reversed(cls.__mro__[:-1]):
        if hasattr(parent, "__annotations__"):
            for name, annotation in parent.__annotations__.items():
                # Skip ClassVar fields
                if get_origin(annotation) is ClassVar:
                    continue

                # Skip fields with excluded types as default values
                field_value = getattr(parent, name, None)
                if isinstance(field_value, ModelPrivateAttr):
                    continue

                all_annotations[name] = annotation

    return all_annotations


def get_actual_type(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        # Handle Optional[T] which is Union[T, None]
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
        return annotation  # Return as-is for complex Union types
    return annotation


def safe_issubclass(cls, class_or_tuple):
    return isinstance(cls, type) and issubclass(cls, class_or_tuple)


def replace_to_redis_types_in_annotation(annotation: Any, type_mapping: Any) -> Any:
    """
    Recursively traverse a type annotation and replace types according to the mapping.
    Handles Union, Optional, Annotated, and other generic types.
    """
    # Direct type replacement
    if annotation in type_mapping:
        new_type = type_mapping[annotation]
        return new_type

    origin = get_origin(annotation)
    args = get_args(annotation)

    # If no origin, it's a simple type (already checked mapping above)
    if origin is None:
        return annotation

    # Handle Annotated specially - preserve metadata
    if origin is Annotated:
        # First arg is the actual type, rest are metadata
        actual_type = args[0]
        metadata = args[1:]

        # Recursively replace in the actual type
        new_type = replace_to_redis_types_in_annotation(actual_type, type_mapping)

        # Reconstruct Annotated with new type and original metadata
        return Annotated[new_type, *metadata]

    # Handle Union, Optional, and other generic types
    if args:
        # Recursively replace types in all arguments
        new_args = tuple(
            replace_to_redis_types_in_annotation(arg, type_mapping) for arg in args
        )

        # Reconstruct the generic type with new arguments
        if origin in type_mapping:
            origin = type_mapping[origin]
        try:
            return origin[new_args]
        except TypeError:
            # Some origins don't support item syntax, return as-is
            return annotation

    return annotation


def find_first_type_in_annotation(annotation: Any) -> type | None:
    origin = get_origin(annotation)
    if origin is None:
        return annotation
    if inspect.isclass(origin):
        return origin
    args = get_args(annotation)

    if args:
        return find_first_type_in_annotation(args[0])

    return None


class RedisTypeTransformer:
    def __init__(self, field_name: str, redis_config: RedisConfig):
        self.field_name = field_name
        self.redis_config = redis_config

    def __getitem__(self, item: type[BaseRedisType]):
        redis_type = self.redis_config.redis_type[item]
        return type(
            redis_type.__name__,
            (redis_type,),
            dict(field_path=self.field_name, original_tyep=item),
        )

    def __contains__(self, item: type[BaseRedisType]):
        return item in self.redis_config.redis_type
