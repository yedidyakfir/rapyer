# RedisPydantic

A Python package that provides Pydantic models with Redis as the backend storage, enabling automatic synchronization between your Python objects and Redis with full type validation.

## Features

- **Async/Await Support**: Built with asyncio for high-performance applications
- **Pydantic Integration**: Full type validation and serialization using Pydantic v2
- **Redis Backend**: Efficient storage using Redis JSON with support for various data types
- **Automatic Serialization**: Handles lists, dicts, BaseModel instances, and primitive types
- **Atomic Operations**: Built-in methods for atomic list and dictionary operations
- **Type Safety**: Full type hints and validation for all Redis operations

## Quick Start

```python
import asyncio
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict
from datetime import datetime

class User(BaseRedisModel):
    name: str
    age: int
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    score: int = 0
    created_at: datetime

async def main():
    # Create a new user
    user = User(name="John", age=30, created_at=datetime.now())
    await user.save()
    
    # Retrieve user by key
    retrieved_user = User()
    retrieved_user.pk = user.pk
    await retrieved_user.name.load()  # Load specific field
    print(f"Retrieved: {retrieved_user.name}")
    
    # Update field directly in Redis
    await user.name.set("John Doe")
    
    # Work with lists
    await user.tags.aappend("python")
    await user.tags.aappend("redis")
    await user.tags.aextend(["pydantic", "async"])
    
    # Work with dictionaries
    await user.metadata.aset_item("department", "engineering")
    await user.metadata.aupdate(role="developer", level="senior")
    
    # Increment counters
    await user.score.set(100)

if __name__ == "__main__":
    asyncio.run(main())
```

## Get Started

Ready to dive in? Check out our [Installation Guide](installation.md) to get started!