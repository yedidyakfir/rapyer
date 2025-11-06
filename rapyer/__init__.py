"""Redis Pydantic - Pydantic models with Redis as the backend."""

from rapyer.base import AtomicRedisModel
from rapyer.init import init_rapyer, teardown_rapyer
from rapyer.types.byte import RedisBytes
from rapyer.types.dct import RedisDict
from rapyer.types.integer import RedisInt
from rapyer.types.lst import RedisList
from rapyer.types.string import RedisStr

__version__ = "0.1.0"
__all__ = [
    "AtomicRedisModel",
    "RedisStr",
    "RedisInt",
    "RedisBytes",
    "RedisList",
    "RedisDict",
    "init_rapyer",
    "teardown_rapyer",
]
