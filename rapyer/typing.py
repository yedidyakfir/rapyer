from typing import Callable

from rapyer.types.base import RedisType

TypeTransformer = Callable[[type], type[RedisType]]
