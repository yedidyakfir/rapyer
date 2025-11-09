# Defining a Model

Creating models in Rapyer is straightforward and follows Pydantic conventions. Models automatically gain atomic Redis operations while maintaining full compatibility with standard Python types.

## Basic Model Definition

```python
from rapyer import AtomicRedisModel
from typing import List, Dict

class User(AtomicRedisModel):
    name: str
    age: int
    email: str
    tags: List[str] = []
    preferences: Dict[str, str] = {}
```

## Using Your Model

Once defined, your model supports both standard Pydantic operations and atomic Redis operations:

```python
import asyncio

async def main():
    # Create a user instance
    user = User(
        name="Alice", 
        age=25, 
        email="alice@example.com",
        tags=["python", "developer"],
        preferences={"theme": "dark", "language": "en"}
    )
    
    # Save to Redis
    await user.save()
    print(f"Saved user with key: {user.key}")
    
    # Perform atomic Redis operations
    await user.tags.aappend("redis")  # Atomic list append
    await user.preferences.aupdate(timezone="UTC")  # Atomic dict update
    
    # Load user from Redis
    loaded_user = await User.get(user.key)
    print(f"Loaded: {loaded_user.name}, Tags: {loaded_user.tags}")
    
    # Delete from Redis
    await user.delete()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuring Redis Connection

Set Redis client and TTL directly on the model's Meta class:

```python
import redis.asyncio as redis
from rapyer import AtomicRedisModel

# Configure Redis client
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True  # IMPORTANT: Always set to True
)

class User(AtomicRedisModel):
    name: str
    age: int

# Configure after class definition
User.Meta.redis = redis_client
User.Meta.ttl = 3600  # Optional: 1 hour TTL
```

## Model Meta Configuration

The `Meta` class allows you to configure model-specific Redis settings:

```python
class User(AtomicRedisModel):
    name: str
    age: int
    
# Available Meta configurations
User.Meta.redis = redis_client    # Redis client instance
User.Meta.ttl = 3600             # Time-to-live in seconds (optional)
```

### TTL (Time To Live)

Set automatic expiration for your models:

```python
class Session(AtomicRedisModel):
    user_id: str
    data: dict = {}

# Sessions expire after 30 minutes
Session.Meta.redis = redis_client
Session.Meta.ttl = 1800  # 30 minutes in seconds
```
