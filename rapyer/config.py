import dataclasses

import redis
from redis.asyncio import Redis


DEFAULT_CONNECTION = "redis://localhost:6379/0"


def create_all_types():
    from rapyer.types.init import ALL_TYPES

    return ALL_TYPES


@dataclasses.dataclass
class RedisConfig:
    redis: Redis = dataclasses.field(
        default_factory=lambda: redis.asyncio.from_url(
            DEFAULT_CONNECTION, decode_responses=True
        )
    )
    redis_type: dict[type, type] = dataclasses.field(default_factory=create_all_types)
    ttl: int | None = None


@dataclasses.dataclass
class RedisFieldConfig:
    field_name: str = ""
