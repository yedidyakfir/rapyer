import dataclasses
from typing import Annotated, Any, Generic, TypeVar


@dataclasses.dataclass(frozen=True)
class KeyAnnotation:
    pass


T = TypeVar("T")


class _KeyType(Generic[T]):
    def __new__(cls, typ: Any = None):
        if typ is None:
            return KeyAnnotation()
        return Annotated[typ, KeyAnnotation()]

    def __class_getitem__(cls, item):
        return Annotated[item, KeyAnnotation()]


# Create the Key callable that works both as a function and generic type
Key = _KeyType
