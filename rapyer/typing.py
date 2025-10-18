from typing import Callable

from rapyer.types.base import BaseRedisType

TypeTransformer = Callable[[type], type[BaseRedisType]]
