# Advanced Features

## Lock Context Manager

Use locks to ensure atomic operations across multiple fields with automatic model synchronization:

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

### Lock Features

- Creates a Redis lock with key `{model_key}/{action}`
- Automatically refreshes the model with latest Redis data on entry
- Saves all changes back to Redis on successful exit
- Ensures atomic operations across multiple field updates

## Pipeline Context Manager

Use pipelines to batch multiple Redis operations for improved performance and atomicity:

```python
class User(BaseRedisModel):
    name: str
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    counter: int = 0

user = User(name="John", tags=["python"], metadata={"role": "developer"})
await user.save()

# Batch multiple operations atomically
async with user.pipeline() as pipelined_user:
    await pipelined_user.tags.aappend("redis")
    await pipelined_user.tags.aextend(["async", "pydantic"])
    await pipelined_user.metadata.aupdate(level="senior", department="engineering")
    await pipelined_user.counter.set(100)
    # All operations are executed atomically when exiting the context
```

### Multiple Model Operations

You can also save multiple models in an atomic action:

```python
user1 = User(name="John", tags=["python"])
user2 = User(name="Jane", tags=["javascript"])
await user1.save()
await user2.save()

async with user1.pipeline():
    await user1.delete()
    await user2.delete()
    # Both deletions are executed atomically
```

### Pipeline Features

- Batches multiple Redis operations into a single atomic transaction
- Automatically refreshes the model with latest Redis data on entry
- Executes all operations atomically when exiting the context
- Improves performance by reducing network round trips
- Ensures data consistency - either all operations succeed or none are applied

### Supported Operations in Pipeline

Most Redis operations work seamlessly in pipeline mode:

```python
async with user.pipeline() as pipelined_user:
    # List operations
    await pipelined_user.tags.aappend("new_tag")
    await pipelined_user.tags.aextend(["tag1", "tag2"])
    await pipelined_user.tags.ainsert(0, "first_tag")
    await pipelined_user.tags.aclear()
    
    # Dictionary operations
    await pipelined_user.metadata.aset_item("key", "value")
    await pipelined_user.metadata.aupdate(key1="val1", key2="val2")
    await pipelined_user.metadata.adel_item("old_key")
    await pipelined_user.metadata.aclear()
    
    # String/Integer operations
    await pipelined_user.name.set("New Name")
    await pipelined_user.counter.set(42)
```

### Pipeline Limitations

Some operations that return values are not supported in pipeline mode:

```python
# These operations won't work in pipeline context:
# - list.apop() - returns removed item
# - dict.apop() - returns removed value  
# - dict.apopitem() - returns removed key-value pair

# Use these operations outside of pipeline context:
popped_tag = await user.tags.apop()
popped_value = await user.metadata.apop("key", "default")
key, value = await user.metadata.apopitem()
```

### Error Handling with Pipeline

If an exception occurs within the pipeline context, no operations are applied to Redis:

```python
try:
    async with user.pipeline() as pipelined_user:
        await pipelined_user.tags.aappend("temp_tag")
        await pipelined_user.metadata.aset_item("temp", "value")
        raise ValueError("Something went wrong")
        # No changes are applied to Redis due to the exception
except ValueError:
    print("Pipeline rolled back - no changes applied")

# User data remains unchanged
final_user = await User.get(user.key)
# Tags and metadata are unchanged from before the pipeline
```

## Model Duplication

Create copies of existing models with new unique keys while preserving all data:

### Basic Duplication

```python
class User(BaseRedisModel):
    name: str
    age: int
    tags: List[str] = []
    metadata: Dict[str, str] = {}

# Create and save original user
original_user = User(name="John", age=30, tags=["python", "redis"])
await original_user.save()

# Create a duplicate with new unique key
duplicate_user = await original_user.duplicate()

# Both users exist independently in Redis
print(f"Original key: {original_user.key}")   # User:uuid1
print(f"Duplicate key: {duplicate_user.key}") # User:uuid2

# Same data, different keys
assert duplicate_user.name == original_user.name
assert duplicate_user.age == original_user.age
assert duplicate_user.tags == original_user.tags
assert duplicate_user.pk != original_user.pk  # Different primary keys
```

### Bulk Duplication

Create multiple duplicates efficiently:

```python
original = User(name="Template User", age=25)
await original.save()

# Create 5 duplicates at once
duplicates = await original.duplicate_many(5)

# All duplicates have unique keys and identical data
for duplicate in duplicates:
    assert duplicate.pk != original.pk
    assert duplicate.name == original.name
    assert duplicate.age == original.age
```

### Working with Duplicated Models

Duplicated models are fully independent and support all Redis operations:

```python
original = User(name="John", tags=["python"])
await original.save()

duplicate = await original.duplicate()

# Modify duplicate independently
await duplicate.tags.aappend("redis")
await duplicate.name.set("John Copy")

# Original remains unchanged
await original.tags.load()
assert original.tags == ["python"]
assert original.name == "John"

# Duplicate has the changes
assert duplicate.tags == ["python", "redis"]
assert duplicate.name == "John Copy"
```

## Working with Nested Models

Rapyer automatically supports nested Pydantic models by converting regular `BaseModel` classes into Redis-enabled versions:

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

### Deep Nesting Support

Rapyer supports unlimited nesting depth:

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

### Nested Model Persistence

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

## TTL (Time To Live) Support

Set expiration times for your models:

```python
class TemporaryModel(BaseRedisModel):
    data: str
    temp_value: int = 0

model = TemporaryModel(data="temporary")
await model.save()

# Set TTL in seconds
await model.set_ttl(300)  # Expires in 5 minutes

# Check remaining TTL
ttl = await model.get_ttl()
print(f"Expires in {ttl} seconds")

# Remove TTL (make persistent)
await model.remove_ttl()
```

## Performance Optimization

### Batch Operations

Use batch operations for better performance:

```python
# Good: Batch multiple list additions
await user.tags.aextend(["tag1", "tag2", "tag3", "tag4"])

# Less efficient: Multiple individual operations
await user.tags.aappend("tag1")
await user.tags.aappend("tag2")
await user.tags.aappend("tag3")
await user.tags.aappend("tag4")

# Good: Batch multiple dict updates
await user.metadata.aupdate(
    role="developer",
    department="engineering",
    level="senior",
    location="remote"
)

# Less efficient: Multiple individual operations
await user.metadata.aset_item("role", "developer")
await user.metadata.aset_item("department", "engineering")
await user.metadata.aset_item("level", "senior")
await user.metadata.aset_item("location", "remote")
```

### Selective Loading

Load only the fields you need:

```python
# Good: Load specific fields
user = User()
user.pk = existing_user_id
await user.name.load()
await user.tags.load()
# Only name and tags are loaded from Redis

# Less efficient: Load entire model
user = await User.get(existing_user_id)
# All fields are loaded from Redis
```

### Connection Pooling

Configure connection pools for high-concurrency applications:

```python
import redis.asyncio as redis

# Create connection pool
pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379/0",
    max_connections=20,
    retry_on_timeout=True,
    socket_keepalive=True
)

class HighPerformanceModel(BaseRedisModel):
    data: str
    
    class Meta:
        redis = redis.Redis(connection_pool=pool)
```

## Error Handling Strategies

### Graceful Degradation

```python
async def safe_redis_operation():
    try:
        user = User(name="test")
        await user.save()
        return user
    except redis.exceptions.ConnectionError:
        # Handle Redis unavailability
        logger.error("Redis unavailable, using fallback")
        return None
    except redis.exceptions.TimeoutError:
        # Handle timeout
        logger.error("Redis operation timed out")
        return None
```

### Retry Logic

```python
import asyncio
from typing import Optional

async def retry_redis_operation(operation, max_retries: int = 3) -> Optional[any]:
    for attempt in range(max_retries):
        try:
            return await operation()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Redis operation failed after {max_retries} attempts: {e}")
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Custom Serialization

For complex types that need custom serialization:

```python
from datetime import datetime
from typing import Any
import json

class CustomSerializationModel(BaseRedisModel):
    timestamp: str  # Store as ISO string
    custom_data: Dict[str, Any] = {}
    
    def set_timestamp(self, dt: datetime):
        """Helper to set datetime as ISO string"""
        await self.timestamp.set(dt.isoformat())
    
    def get_timestamp(self) -> datetime:
        """Helper to get datetime from ISO string"""
        return datetime.fromisoformat(self.timestamp)
    
    async def set_custom_object(self, obj: Any):
        """Serialize complex object to JSON"""
        json_str = json.dumps(obj, default=str)
        await self.custom_data.aset_item("serialized", json_str)
```