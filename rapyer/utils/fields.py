import inspect
from typing import get_origin, ClassVar, get_args, Any, Callable

from pydantic import TypeAdapter
from pydantic.fields import ModelPrivateAttr


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
