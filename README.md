# RedisPydantic

A Python package that provides Pydantic models with Redis as the backend storage, enabling automatic synchronization between your Python objects and Redis with full type validation.

## Features

- **Async/Await Support**: Built with asyncio for high-performance applications
- **Pydantic Integration**: Full type validation and serialization using Pydantic v2
- **Redis Backend**: Efficient storage using Redis JSON with support for various data types
- **Automatic Serialization**: Handles lists, dicts, BaseModel instances, and primitive types
- **Atomic Operations**: Built-in methods for atomic list and dictionary operations
- **Type Safety**: Full type hints and validation for all Redis operations

## Installation

```bash
pip install redis-pydantic
```

## Requirements

- Python 3.10+
- Redis server with JSON module
- Pydantic v2
- redis-py with async support

## Quick Start

```python
import asyncio
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict

class User(BaseRedisModel):
    name: str
    age: int
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    score: int = 0

async def main():
    # Create a new user
    user = User(name="John", age=30)
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

## Redis Connection Setup

### Default Connection

By default, RedisPydantic connects to `redis://localhost:6379/0`. 

### Custom Connection

Configure Redis connection in your model's `Meta` class:

```python
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url("redis://your-redis-host:6379/1")
```

### Environment-based Configuration

```python
import os
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url(redis_url)
```

### Connection with Authentication

```python
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url(
            "redis://username:password@your-redis-host:6379/0",
            decode_responses=True
        )
```

## Supported Types and Operations

### String (RedisStr)

```python
class MyModel(BaseRedisModel):
    name: str = "default"

# Operations
await model.name.set("new_value")  # Set string value
await model.name.load()            # Load from Redis
```

### Integer (RedisInt)

```python
class MyModel(BaseRedisModel):
    counter: int = 0

# Operations
await model.counter.set(42)        # Set integer value
await model.counter.load()         # Load from Redis
```

### Boolean (RedisBool)

```python
class MyModel(BaseRedisModel):
    is_active: bool = True

# Operations
await model.is_active.set(False)   # Set boolean value
await model.is_active.load()       # Load from Redis
```

### Bytes (RedisBytes)

```python
class MyModel(BaseRedisModel):
    data: bytes = b""

# Operations
await model.data.set(b"binary_data")  # Set bytes value
await model.data.load()               # Load from Redis
```

### List (RedisList)

```python
class MyModel(BaseRedisModel):
    items: List[str] = []

# Operations
await model.items.aappend("item1")           # Append single item
await model.items.aextend(["item2", "item3"]) # Extend with multiple items
await model.items.ainsert(0, "first")        # Insert at specific index
popped = await model.items.apop()            # Pop last item
popped = await model.items.apop(0)           # Pop item at index
await model.items.aclear()                   # Clear all items
await model.items.load()                     # Load from Redis
```

### Dictionary (RedisDict)

```python
class MyModel(BaseRedisModel):
    metadata: Dict[str, str] = {}

# Operations
await model.metadata.aset_item("key", "value")     # Set single item
await model.metadata.aupdate(key1="val1", key2="val2")  # Update multiple items
await model.metadata.adel_item("key")               # Delete item
popped = await model.metadata.apop("key")           # Pop item by key
popped = await model.metadata.apop("key", "default") # Pop with default
key, value = await model.metadata.apopitem()        # Pop arbitrary item
await model.metadata.aclear()                       # Clear all items
await model.metadata.load()                         # Load from Redis
```

## Advanced Usage

### Lock Context Manager

Use the lock context manager to ensure atomic operations across multiple fields with automatic model synchronization:

```python
class User(BaseRedisModel):
    name: str
    balance: int = 0
    transaction_count: int = 0

user = User(name="John", balance=1000)
await user.save()

# Lock with default action
async with user.lock() as locked_user:
    # The locked_user is automatically refreshed from Redis
    locked_user.balance -= 50
    locked_user.transaction_count += 1
    # Changes are automatically saved when exiting the context

# Lock with specific action name
async with user.lock("transfer") as locked_user:
    # This creates a lock with key "User:user_id/transfer"
    locked_user.balance -= 100
    locked_user.transaction_count += 1
    # Automatic save on context exit
```

The lock context manager:
- Creates a Redis lock with key `{model_key}/{action}`
- Automatically refreshes the model with latest Redis data on entry
- Saves all changes back to Redis on successful exit
- Ensures atomic operations across multiple field updates

### Working with Nested Models

RedisPydantic automatically supports nested Pydantic models by converting regular `BaseModel` classes into Redis-enabled versions. This allows you to use all Redis field operations on nested model fields.

```python
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    bio: str = ""
    skills: List[str] = Field(default_factory=list)
    settings: Dict[str, bool] = Field(default_factory=dict)

class Address(BaseModel):
    street: str
    city: str
    country: str = "US"

class User(BaseRedisModel):
    name: str
    profile: UserProfile = Field(default_factory=UserProfile)
    address: Address
    tags: List[str] = Field(default_factory=list)

user = User(name="John", address=Address(street="123 Main St", city="Boston"))
await user.save()

# Access Redis operations on nested model fields
await user.profile.skills.aappend("Python")
await user.profile.skills.aextend(["Redis", "AsyncIO"])
await user.profile.settings.aupdate(dark_mode=True, notifications=False)

# Even deeply nested operations work
await user.profile.skills.ainsert(0, "Leadership")
popped_skill = await user.profile.skills.apop()

# All Redis list/dict operations are available on nested fields
await user.profile.settings.aset_item("email_updates", True)
await user.profile.settings.adel_item("notifications")

# Load specific nested fields
await user.profile.skills.load()
await user.profile.settings.load()

print(user.profile.skills)    # Reflects Redis state
print(user.profile.settings)  # Reflects Redis state
```

#### Deep Nesting Support

RedisPydantic supports unlimited nesting depth:

```python
class InnerModel(BaseModel):
    items: List[str] = Field(default_factory=list)
    counter: int = 0

class MiddleModel(BaseModel):
    inner: InnerModel = Field(default_factory=InnerModel)
    tags: List[str] = Field(default_factory=list)

class OuterModel(BaseRedisModel):
    middle: MiddleModel = Field(default_factory=MiddleModel)
    data: Dict[str, int] = Field(default_factory=dict)

outer = OuterModel()
await outer.save()

# All Redis operations work at any nesting level
await outer.middle.inner.items.aappend("deep_item")
await outer.middle.tags.aextend(["tag1", "tag2"])
await outer.data.aset_item("count", 42)

# Load nested data
await outer.middle.inner.items.load()
await outer.middle.tags.load()
```

#### Nested Model Persistence

Nested models maintain full persistence and consistency:

```python
# Create and modify nested data
user1 = User(name="Alice", address=Address(street="456 Oak Ave", city="Seattle"))
await user1.save()
await user1.profile.skills.aextend(["JavaScript", "TypeScript"])

# Access from different instance
user2 = User()
user2.pk = user1.pk
await user2.profile.skills.load()
print(user2.profile.skills)  # ["JavaScript", "TypeScript"]

# All operations are atomic and persistent
await user2.profile.skills.aappend("React")
await user1.profile.skills.load()  # user1 now sees the new skill
```

### Working with Nested Types

```python
class User(BaseRedisModel):
    preferences: Dict[str, List[str]] = {}
    scores: List[int] = []

user = User()

# Nested operations
await user.preferences.aset_item("languages", ["python", "rust"])
await user.scores.aextend([95, 87, 92])
```

### Loading Specific Fields

```python
user = User()
user.pk = "some-existing-id"

# Load only specific fields from Redis
await user.name.load()
await user.tags.load()
# Other fields remain unloaded
```

### Atomic Operations

All Redis operations are atomic. For example:

```python
# This is atomic - either both operations succeed or both fail
await user.metadata.aupdate(
    last_login=str(datetime.now()),
    session_count=str(session_count + 1)
)

# This is also atomic
popped_item = await user.items.apop()  # Atomically removes and returns
```

### Model Serialization

```python
# Get the model as a Redis-compatible dict
redis_data = user.redis_dump()

# Save entire model to Redis
await user.save()
```

## Key Features

### Automatic Type Conversion

RedisPydantic handles serialization and deserialization automatically:

```python
class MyModel(BaseRedisModel):
    data: bytes = b""

model = MyModel()
await model.data.set(b"binary_data")  # Automatically base64 encoded in Redis
loaded_data = await model.data.load()  # Automatically decoded back to bytes
```

### Type Safety

All operations maintain type safety:

```python
class MyModel(BaseRedisModel):
    count: int = 0

# This will raise TypeError
await model.count.set("not_a_number")  # ❌ TypeError: Value must be int

# This works
await model.count.set(42)  # ✅ Valid
```

### Consistent Local and Redis State

RedisPydantic keeps your local Python objects in sync with Redis:

```python
user = User(tags=["python"])
await user.save()

await user.tags.aappend("redis")  # Updates both local list and Redis
print(user.tags)  # ["python", "redis"] - local state is updated
```

## Error Handling

```python
try:
    # Attempt to pop from empty list
    item = await user.tags.apop()
except IndexError:
    print("List is empty")

try:
    # Attempt to pop non-existent key from dict
    value = await user.metadata.apop("nonexistent_key")
except KeyError:
    print("Key not found")

# Using default values
value = await user.metadata.apop("key", "default_value")  # Returns default if key missing
```

## Performance Tips

1. **Batch Operations**: Use `aupdate()` for multiple dict updates and `aextend()` for multiple list items
2. **Load Only What You Need**: Load specific fields instead of entire models when possible
3. **Use Appropriate Data Types**: Choose the right Redis type for your use case
4. **Connection Pooling**: Configure Redis connection pools for high-concurrency applications

## Examples

### User Session Management

```python
class UserSession(BaseRedisModel):
    user_id: str
    session_data: Dict[str, str] = {}
    activity_log: List[str] = []
    is_active: bool = True
    last_seen: str = ""

session = UserSession(user_id="user123")
await session.save()

# Track user activity
await session.activity_log.aappend(f"login:{datetime.now()}")
await session.session_data.aupdate(
    ip_address="192.168.1.1",
    user_agent="Chrome/91.0"
)
```

### Shopping Cart

```python
class ShoppingCart(BaseRedisModel):
    user_id: str
    items: List[str] = []  # product IDs
    quantities: Dict[str, int] = {}
    total_amount: int = 0  # in cents

cart = ShoppingCart(user_id="user456")

# Add items
await cart.items.aappend("product123")
await cart.quantities.aset_item("product123", 2)

# Update totals
await cart.total_amount.set(4999)  # $49.99
```

### Configuration Management

```python
class AppConfig(BaseRedisModel):
    features: Dict[str, bool] = {}
    limits: Dict[str, int] = {}
    allowed_ips: List[str] = []

config = AppConfig()

# Enable feature flags
await config.features.aupdate(
    new_ui=True,
    beta_features=False
)

# Set rate limits
await config.limits.aupdate(
    requests_per_minute=1000,
    max_file_size=10485760
)
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.