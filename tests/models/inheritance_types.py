from datetime import datetime
from typing import Any
from enum import Enum

from pydantic import Field, BaseModel
from rapyer.base import AtomicRedisModel


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class BaseUserModel(AtomicRedisModel):
    name: str = "default_user"
    email: str = Field(default="user@example.com")
    age: int = Field(default=25, ge=0, le=150)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    role: UserRole = UserRole.USER
    optional_field: str | None = None
    scores: list[int] = Field(default_factory=lambda: [100, 200])


class AdminUserModel(BaseUserModel):
    admin_level: int = Field(default=1, ge=1, le=10)
    permissions: list[str] = Field(default_factory=lambda: ["read", "write"])
    managed_users: dict[str, str] = Field(default_factory=dict)
    last_login: datetime = Field(default_factory=datetime.now)
    is_super_admin: bool = False
    admin_notes: str = "No notes"
    backup_email: str | None = None
    access_codes: list[int] = Field(default_factory=lambda: [1001, 1002])


# Models for testing inheritance scenarios


class SimpleBaseModel(BaseModel):
    username: str = "test_user"
    score: int = 100
    active: bool = True


class HybridModel(AtomicRedisModel, SimpleBaseModel):
    redis_field: str = "redis_value"
    count: int = 42


class SimpleInheritanceBaseModel(BaseModel):
    name: str = "default_name"
    value: int = 10


class NonPydanticClass:
    def __init__(self):
        self.non_pydantic_field = "should_not_persist"
        self.another_field = 999
        self.temp_data = {"key": "value"}


class MixedInheritanceModel(AtomicRedisModel, NonPydanticClass):
    redis_data: str = "test_data"
    number: int = 123

    model_config = {"extra": "allow"}

    def __init__(self, **data):
        AtomicRedisModel.__init__(self, **data)
        NonPydanticClass.__init__(self)


class HybridRedisModel(AtomicRedisModel, SimpleInheritanceBaseModel, NonPydanticClass):
    additional_field: str = "extra_data"

    model_config = {"extra": "allow"}

    def __init__(self, **data):
        AtomicRedisModel.__init__(self, **data)
        SimpleInheritanceBaseModel.__init__(self, **data)
        NonPydanticClass.__init__(self)
