from pydantic import Field

from rapyer.base import AtomicRedisModel


class UserModel(AtomicRedisModel):
    tags: list[str] = Field(default_factory=list)
