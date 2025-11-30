# For python 3.10 support
try:
    from typing import Self, Unpack
except ImportError:
    from typing_extensions import Self, Unpack

__all__ = ["Self", "Unpack"]
