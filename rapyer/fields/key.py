import dataclasses
from typing import Annotated, TypeAlias

from typing import TypeVar, TypeAliasType

T = TypeVar("T")

# Turn your dynamic factory into a proper generic alias
KeyT = TypeAliasType("KeyT", T, type_params=(T,))


@dataclasses.dataclass(frozen=True)
class KeyAnnotation:
    pass


def Key(typ: type = None) -> TypeAlias:
    if typ is None:
        return KeyAnnotation()

    return Annotated[typ, KeyAnnotation()]
