import abc
from abc import ABC
from types import UnionType
from typing import get_origin, Union, get_args, Any, Annotated


class TypeConverter(ABC):
    @abc.abstractmethod
    def is_type_support(self, type_to_check: type) -> bool:
        pass

    @abc.abstractmethod
    def convert_flat_type(self, type_to_convert: type) -> type:
        pass

    @abc.abstractmethod
    def covert_generic_type(
        self, type_to_covert: type, generic_values: tuple[type]
    ) -> type:
        pass


def replace_to_redis_types_in_annotation(
    annotation: Any, type_converter: TypeConverter
) -> Any:
    """
    Recursively traverse a type annotation and replace types according to the mapping.
    Handles Union, Optional, Annotated, and other generic types.
    """
    # Direct type replacement
    if type_converter.is_type_support(annotation):
        new_type = type_converter.convert_flat_type(annotation)
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
        new_type = replace_to_redis_types_in_annotation(actual_type, type_converter)

        # Reconstruct Annotated with new type and original metadata
        annotated_args = (new_type,) + metadata
        return Annotated[annotated_args]

    # Handle Union, Optional, and other generic types
    if args:
        # Recursively replace types in all arguments
        new_args = tuple(
            [replace_to_redis_types_in_annotation(arg, type_converter) for arg in args]
        )

        # Reconstruct the generic type with new arguments
        if type_converter.is_type_support(origin):
            origin = type_converter.covert_generic_type(origin, new_args)
        elif origin is UnionType:
            origin = Union[new_args]
        # This is for optional support
        elif origin is Union:
            origin = Union[new_args]
        else:
            # If we don't support the origin, just use the original annotation
            origin = annotation
        return origin
    return annotation
