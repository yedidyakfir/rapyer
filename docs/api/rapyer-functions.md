# Rapyer Functions

This page documents the global functions available in the rapyer package for working with Redis models.

## get()

```python
async def get(redis_key: str) -> AtomicRedisModel
```

Retrieves a model instance from Redis by its key, automatically determining the correct model class.

### Parameters

- **redis_key** (`str`): The Redis key of the model instance to retrieve

### Returns

- **AtomicRedisModel**: The model instance corresponding to the Redis key

### Raises

- **KeyError**: If the model class cannot be determined from the key
- **ValueError**: If the key format is invalid

### Description

The `get()` function provides a global way to retrieve any model instance from Redis without knowing its specific class beforehand. It works by:

1. Extracting the class name from the Redis key format (`ClassName:instance_id`)
2. Looking up the appropriate model class from the registered Redis models
3. Calling the class-specific `get()` method to retrieve and deserialize the instance

This is particularly useful when you have multiple model types and want a unified retrieval mechanism, or when working with keys of unknown model types.

### Example

```python
import asyncio
import rapyer
from rapyer import AtomicRedisModel


class User(AtomicRedisModel):
    name: str
    age: int
    email: str


class Product(AtomicRedisModel):
    name: str
    price: float
    in_stock: bool


async def main():
    # Create and save different model types
    user = User(name="Alice", age=30, email="alice@example.com")
    product = Product(name="Laptop", price=999.99, in_stock=True)

    await user.asave()
    await product.asave()

    # Retrieve using global get function
    retrieved_user = await rapyer.aget(user.key)
    retrieved_product = await rapyer.aget(product.key)

    print(f"User: {retrieved_user.name}, Age: {retrieved_user.age}")
    print(f"Product: {retrieved_product.name}, Price: {retrieved_product.price}")

    # The function automatically returns the correct model type
    print(f"User type: {type(retrieved_user).__name__}")
    print(f"Product type: {type(retrieved_product).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
```

## find_redis_models()

```python
def find_redis_models() -> list[type[AtomicRedisModel]]
```

Returns a list of all registered Redis model classes.

### Parameters

None

### Returns

- **list[type[AtomicRedisModel]]**: A list containing all model classes that inherit from `AtomicRedisModel`

### Description

The `find_redis_models()` function provides access to all Redis model classes that have been defined and registered in the application.

## afind()

```python
@classmethod
async def afind(cls) -> list[AtomicRedisModel]
```

Retrieves all instances of a specific model class from Redis.

### Parameters

None

### Returns

- **list[AtomicRedisModel]**: A list containing all instances of the model class stored in Redis

### Description

The `afind()` method is a class method that retrieves all instances of a particular model class from Redis. It works by:

1. Finding all Redis keys that match the model's key pattern using `afind_keys()`
2. Performing a batch retrieval of all matching records using Redis JSON's `mget` operation
3. Deserializing each record back into the appropriate model instance

This method is efficient for retrieving multiple instances as it uses Redis's bulk operations rather than individual get operations.

### Example

```python
import asyncio
from rapyer import AtomicRedisModel


class User(AtomicRedisModel):
    name: str
    age: int
    email: str


class Product(AtomicRedisModel):
    name: str
    price: float
    in_stock: bool


async def main():
    # Create and save multiple users
    users = [
        User(name="Alice", age=30, email="alice@example.com"),
        User(name="Bob", age=25, email="bob@example.com"),
        User(name="Charlie", age=35, email="charlie@example.com")
    ]

    products = [
        Product(name="Laptop", price=999.99, in_stock=True),
        Product(name="Mouse", price=29.99, in_stock=False)
    ]

    # Save all instances
    for user in users:
        await user.asave()
    for product in products:
        await product.asave()

    # Find all users and products
    all_users = await User.afind()
    all_products = await Product.afind()

    print(f"Found {len(all_users)} users:")
    for user in all_users:
        print(f"  - {user.name} ({user.age})")

    print(f"Found {len(all_products)} products:")
    for product in all_products:
        print(f"  - {product.name}: ${product.price}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Note

The `afind()` method only returns instances of the specific model class it's called on. To find all instances across different model types, you would need to call `afind()` on each model class separately.
