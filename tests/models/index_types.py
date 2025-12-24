from datetime import datetime

from rapyer import AtomicRedisModel
from rapyer.fields import Index, Key


# Basic Index Models
class IndexTestModel(AtomicRedisModel):
    name: Index[str]
    age: Index[int]
    description: str


# Inheritance Models with Index
class BaseIndexModel(AtomicRedisModel):
    id: Index[str]
    created_at: Index[datetime]


class UserIndexModel(BaseIndexModel):
    username: Index[str]
    email: str


class ProductIndexModel(BaseIndexModel):
    name: Index[str]
    price: Index[float]


# Nested Models with Keys and Index
class AddressModel(AtomicRedisModel):
    street: Index[str]
    city: Index[str]


class PersonModel(AtomicRedisModel):
    name: Index[str]
    email: Key[str]
    address: AddressModel
