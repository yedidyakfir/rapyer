# Basic Usage

## Model Lifecycle

### Creating Models

```python
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict

class User(BaseRedisModel):
    name: str
    age: int
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    score: int = 0

# Create instance
user = User(name="John", age=30)
```

### Saving Models

```python
# Save to Redis
await user.save()

# The model now has a unique key
print(user.key)  # User:uuid-string
print(user.pk)   # uuid-string
```

### Loading Models

```python
# Load by key
loaded_user = await User.get(user.key)

# Or create instance and set key manually
user2 = User()
user2.pk = user.pk
await user2.load()  # Load all fields
```

### Deleting Models

```python
# Delete from Redis
await user.delete()

# Or delete by key without loading
success = await User.try_delete(key)
```

## Field Operations

### Loading Specific Fields

Instead of loading the entire model, you can load specific fields:

```python
user = User()
user.pk = "existing-user-id"

# Load only the name field
await user.name.load()
print(user.name)  # Now contains the Redis value

# Load multiple fields
await user.name.load()
await user.age.load()
```

### Setting Field Values

```python
# Set string field
await user.name.set("New Name")

# Set integer field
await user.age.set(35)

# Set boolean field (if you have one)
await user.is_active.set(True)
```

## Working with Collections

### Lists

```python
# Add single item
await user.tags.aappend("python")

# Add multiple items
await user.tags.aextend(["redis", "pydantic", "async"])

# Insert at specific position
await user.tags.ainsert(0, "first-tag")

# Remove items
last_item = await user.tags.apop()      # Remove last
first_item = await user.tags.apop(0)    # Remove first

# Clear all items
await user.tags.aclear()

# Load current state
await user.tags.load()
print(user.tags)  # Current list from Redis
```

### Dictionaries

```python
# Set single item
await user.metadata.aset_item("department", "engineering")

# Update multiple items
await user.metadata.aupdate(
    role="developer",
    level="senior",
    location="remote"
)

# Remove items
await user.metadata.adel_item("location")

# Pop items (remove and return)
role = await user.metadata.apop("role")
role_with_default = await user.metadata.apop("role", "unknown")

# Pop arbitrary item
key, value = await user.metadata.apopitem()

# Clear all items
await user.metadata.aclear()

# Load current state
await user.metadata.load()
print(user.metadata)  # Current dict from Redis
```

## Data Consistency

### Local vs Redis State

RedisPydantic keeps your local Python objects in sync with Redis:

```python
user = User(name="John", tags=["python"])
await user.save()

# When you modify through Redis operations, local state updates
await user.tags.aappend("redis")
print(user.tags)  # ["python", "redis"] - local state updated

# When you load specific fields, only those fields are updated
user.name = "Local Name"  # Local change
await user.tags.load()   # Only tags loaded from Redis
print(user.name)         # Still "Local Name"
```

### Manual Synchronization

```python
# Force reload all fields from Redis
await user.load()

# Save all local changes to Redis
await user.save()
```

## Error Handling

### Common Exceptions

```python
try:
    # Pop from empty list
    item = await user.tags.apop()
except IndexError:
    print("List is empty")

try:
    # Pop non-existent key from dict
    value = await user.metadata.apop("nonexistent")
except KeyError:
    print("Key not found")

# Use default values to avoid exceptions
value = await user.metadata.apop("key", "default")
```

### Connection Errors

```python
import redis.exceptions

try:
    await user.save()
except redis.exceptions.ConnectionError:
    print("Could not connect to Redis")
except redis.exceptions.TimeoutError:
    print("Redis operation timed out")
```

## Best Practices

### 1. Load Only What You Need

```python
# Good: Load specific fields
await user.name.load()
await user.age.load()

# Less efficient: Load entire model
await user.load()
```

### 2. Use Batch Operations

```python
# Good: Update multiple items at once
await user.metadata.aupdate(
    role="developer",
    department="engineering",
    level="senior"
)

# Less efficient: Multiple individual operations
await user.metadata.aset_item("role", "developer")
await user.metadata.aset_item("department", "engineering")
await user.metadata.aset_item("level", "senior")
```

### 3. Handle Defaults Gracefully

```python
# Good: Use default values
role = await user.metadata.apop("role", "unknown")

# Less robust: Exception handling
try:
    role = await user.metadata.apop("role")
except KeyError:
    role = "unknown"
```

### 4. Use Appropriate Data Types

```python
# Good: Use appropriate Redis types
class User(BaseRedisModel):
    tags: List[str] = []          # For ordered collections
    metadata: Dict[str, str] = {} # For key-value pairs
    score: int = 0                # For numeric values

# Less efficient: Store everything as strings
class User(BaseRedisModel):
    tags_json: str = "[]"         # Don't do this
    metadata_json: str = "{}"     # Don't do this
```