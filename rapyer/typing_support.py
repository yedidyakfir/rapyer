# For python 3.10 support
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

__all__ = ["Self"]
