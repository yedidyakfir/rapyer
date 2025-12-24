from datetime import datetime

from rapyer import AtomicRedisModel
from rapyer.fields import Index, Key


# Basic Index Models
class IndexTestModel1(AtomicRedisModel):
    name: Index[str]
    age: Index[int]
    description: str


class IndexTestModel2(AtomicRedisModel):
    name: Index[str]
    city: Index[str]
    score: Index[float]
    age: int  # No longer indexed


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
    zip_code: Key[str]


class PersonModel(AtomicRedisModel):
    name: Index[str]
    email: Key[str]
    address: AddressModel


class CompanyModel(AtomicRedisModel):
    name: Index[str]
    headquarters: AddressModel
    # Note: For simplicity, using a single branch office instead of list
    # as list indexing is more complex
    branch_office: AddressModel
