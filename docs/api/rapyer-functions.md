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
    
    await user.save()
    await product.save()
    
    # Retrieve using global get function
    retrieved_user = await rapyer.get(user.key)
    retrieved_product = await rapyer.get(product.key)
    
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
