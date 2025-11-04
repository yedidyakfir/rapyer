from datetime import datetime
from typing import Any
from enum import Enum

from pydantic import Field
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
