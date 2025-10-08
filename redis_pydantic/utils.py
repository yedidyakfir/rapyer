import asyncio
import contextlib
import uuid
from datetime import timedelta
from typing import get_origin, ClassVar, Union, get_args, Any

from pydantic.fields import ModelPrivateAttr
from redis.asyncio import Redis


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
