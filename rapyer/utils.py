import asyncio
import contextlib
import inspect
import uuid
from datetime import timedelta
from types import UnionType
from typing import get_origin, ClassVar, Union, get_args, Any, Annotated, Callable

from pydantic import TypeAdapter
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
    return inspect.isclass(cls) and issubclass(cls, class_or_tuple)


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
        # The first arg is the actual type, rest are metadata
        actual_type = args[0]
        metadata = args[1:]

        # Recursively replace the actual type
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
            origin = type_mapping[origin, new_args]
        if origin is UnionType:
            origin = Union
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


def convert_field_factory_type(original_factory: Callable, adapter: TypeAdapter):
    original_value = original_factory()
    return adapter.validate_python(original_value)


def _collect_annotations_recursive(
    current_cls, exclude_classes, all_annotations, visited
):
    """
    Helper functions to recursively collect annotations.

    Args:
        current_cls: Current class being processed
        exclude_classes: Set of classes to exclude
        all_annotations: Dictionary to store collected annotations
        visited: Set of already visited classes
    """
    # Avoid infinite loops
    if current_cls in visited:
        return
    visited.add(current_cls)

    # Stop if this is an excluded class
    if current_cls in exclude_classes:
        return

    # First, recursively process parent classes
    for base in current_cls.__bases__:
        # Skip object class
        if base is object:
            continue
        _collect_annotations_recursive(base, exclude_classes, all_annotations, visited)

    # Then add current class annotations (overriding parents)
    if hasattr(current_cls, "__annotations__"):
        for name, annotation in current_cls.__annotations__.items():
            # Skip private fields (starting with _)
            if name.startswith("_"):
                continue

            # Skip ClassVar annotations
            if get_origin(annotation) is ClassVar:
                continue

            # Skip fields with excluded types as default values
            field_value = getattr(current_cls, name, None)
            if isinstance(field_value, ModelPrivateAttr):
                continue

            all_annotations[name] = annotation


def get_all_annotations(cls, exclude_classes=None):
    """
    Recursively get all annotations from a class and its parent classes.
    Excludes private fields (starting with _) and ClassVar annotations.

    Args:
        cls: The class to inspect
        exclude_classes: Set/tuple of classes where recursion should stop

    Returns:
        dict: Merged annotations from the class hierarchy
    """
    if exclude_classes is None:
        exclude_classes = set()
    elif not isinstance(exclude_classes, set):
        exclude_classes = set(exclude_classes)

    all_annotations = {}
    visited = set()

    _collect_annotations_recursive(cls, exclude_classes, all_annotations, visited)

    return all_annotations
