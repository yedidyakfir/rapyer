from enum import Enum

from pydantic import Field, BaseModel


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Person(BaseModel):
    name: str
    age: int
    email: str


class Company(BaseModel):
    name: str
    employees: int
    founded: int


class User(BaseModel):
    id: int
    name: str
    email: str


class Product(BaseModel):
    name: str
    price: int  # Changed from float to int since float isn't supported
    in_stock: bool


class UserProfile(BaseModel):
    name: str
    age: int
    email: str


class NestedConfig(BaseModel):
    settings: dict[str, str] = Field(default_factory=dict)
    options: list[str] = Field(default_factory=list)


class Address(BaseModel):
    street: str
    city: str
    zip_code: str


class Settings(BaseModel):
    preferences: dict[str, str] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)
