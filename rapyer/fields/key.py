import dataclasses
from typing import Annotated


@dataclasses.dataclass(frozen=True)
class KeyAnnotation:
    pass


def Key(typ: type = None):
    if typ is None:
        return KeyAnnotation()

    return Annotated[typ, KeyAnnotation()]
