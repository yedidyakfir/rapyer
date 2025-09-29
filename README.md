# Redis Pydantic

A Python package that provides Pydantic models with Redis as the backend storage.

## Features

- **Async/Await Support**: Built with asyncio for high-performance applications
- **Pydantic Integration**: Full type validation and serialization using Pydantic v2
- **Redis Backend**: Efficient storage using Redis with support for various data types
- **Automatic Serialization**: Handles lists, dicts, BaseModel instances, and primitive types
- **Field Operations**: Built-in methods for list operations and counter increments

## Installation

```bash
pip install redis-pydantic
```

## Quick Start

```python
import asyncio
from redis_pydantic import RedisModel
from typing import List

class User(RedisModel):
    name: str
    age: int
    tags: List[str] = []
    score: int = 0

async def main():
    # Create a new user
    user = User(name="John", age=30)
    await user.save()
    
    # Retrieve user by key
    retrieved_user = await User.get(user.key)
    print(f"Retrieved: {retrieved_user.name}, {retrieved_user.age}")
    
    # Update user
    await user.update(age=31)
    
    # Append to list
    await user.append_to_list("tags", "python")
    await user.append_to_list("tags", "redis")
    
    # Increase counter
    await user.increase_counter("score", 10)
    
    # Delete user
    await user.delete()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

By default, Redis Pydantic connects to `redis://localhost:6379/0`. You can configure the connection by setting the `redis` attribute in your model's `Config` class:

```python
import redis.asyncio as redis
from redis_pydantic import RedisModel

class MyModel(RedisModel):
    name: str
    
    class Config:
        redis = redis.from_url("redis://your-redis-host:6379/1")
```

## API Reference

### RedisModel

The base class for all Redis-backed Pydantic models.

#### Methods

- `save()`: Save the model to Redis
- `update(**kwargs)`: Update specific fields
- `delete()`: Delete the model from Redis
- `get(key: str)`: Class method to retrieve a model by key
- `append_to_list(list_name: str, value: Any)`: Append a value to a list field
- `increase_counter(counter_name: str, value: int = 1)`: Increment a counter field

#### Class Methods

- `update_from_id(redis_id: str, **kwargs)`: Update a model by its Redis key
- `delete_from_key(key: str)`: Delete a model by its Redis key
- `append_to_list_from_key(key: str, list_name: str, value: Any)`: Append to list by key
- `increase_counter_from_key(key: str, counter_name: str, value: int = 1)`: Increment counter by key

## Data Types

Redis Pydantic supports the following field types:

- **Primitives**: `str`, `int`, `float`, `bool`
- **Collections**: `List`, `Dict`
- **Pydantic Models**: Nested `BaseModel` instances
- **Custom Types**: Any type that can be serialized to JSON

## Requirements

- Python 3.11+
- Redis server
- Pydantic v2
- redis-py with async support

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.