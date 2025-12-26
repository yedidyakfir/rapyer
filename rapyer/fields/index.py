import dataclasses
from typing import Annotated, Any, Generic, TypeVar


@dataclasses.dataclass(frozen=True)
class IndexAnnotation:
    pass


T = TypeVar("T")


class _IndexType(Generic[T]):
    def __new__(cls, typ: Any = None):
        if typ is None:
            return IndexAnnotation()
        return Annotated[typ, IndexAnnotation()]

    def __class_getitem__(cls, item):
        return Annotated[item, IndexAnnotation()]


Index = _IndexType