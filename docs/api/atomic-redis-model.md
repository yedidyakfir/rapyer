# API Reference

This page provides a comprehensive reference of all available functions and methods in the Rapyer package.

## AtomicRedisModel

The `AtomicRedisModel` is the core class that all Redis-backed models inherit from. It provides atomic operations and seamless integration with Redis as a backend storage.

### Properties

#### `pk`
**Type:** `str`  
**Description:** Primary key of the model. If a key field is defined using `KeyAnnotation`, returns that field's value; otherwise returns the internal UUID.

```python
user = User(name="John", age=30)
print(user.pk)  # Returns UUID if no key field defined
```

#### `key`
**Type:** `str`  
**Description:** The Redis key used to store this model instance. Format: `{ClassName}:{pk}`

```python
user = User(name="John")
print(user.key)  # "User:abc-123-def-456"
```

#### `field_name`
**Type:** `str`  
**Description:** The field name when this model is used as a nested field in another model.

#### `field_path`
**Type:** `str`  
**Description:** The full JSON path to this model when nested, including parent paths.

#### `json_path`
**Type:** `str`  
**Description:** The JSON path used for Redis JSON operations. Returns `"$"` for root level or `"${field_path}"` for nested models.

### Instance Methods

#### `save()`
**Type:** `async` method  
**Returns:** `Self`  
**Description:** Saves the current model instance to Redis using JSON.SET operation.

```python
user = User(name="John", age=30)
await user.save()
```

#### `load()`
**Type:** `async` method  
**Returns:** `Self`  
**Description:** Loads the latest data from Redis for this model instance, updating the current instance.

```python
await user.load()  # Refreshes user with latest Redis data
```

#### `delete()`
**Type:** `async` method  
**Returns:** `bool`  
**Description:** Deletes this model instance from Redis. Can only be called on top-level models (not nested ones).

```python
success = await user.delete()
```

#### `duplicate()`
**Type:** `async` method  
**Returns:** `Self`  
**Description:** Creates a duplicate of the current model with a new primary key and saves it to Redis.

```python
user_copy = await user.duplicate()
```

#### `duplicate_many(num)`
**Type:** `async` method  
**Parameters:** 
- `num` (int): Number of duplicates to create  
**Returns:** `list[Self]`  
**Description:** Creates multiple duplicates of the current model.

```python
user_copies = await user.duplicate_many(5)  # Creates 5 duplicates
```

#### `update(**kwargs)`
**Type:** Synchronous method  
**Parameters:** 
- `**kwargs`: Field values to update  
**Description:** Updates model fields locally (does not save to Redis).

```python
user.update(name="Jane", age=25)
```

#### `aupdate(**kwargs)`
**Type:** `async` method  
**Parameters:** 
- `**kwargs`: Field values to update  
**Description:** Updates specified fields both locally and in Redis atomically.

```python
await user.aupdate(name="Jane", age=25)
```

#### `is_inner_model()`
**Type:** Synchronous method  
**Returns:** `bool`  
**Description:** Returns True if this model is a nested field within another model.

```python
if user.is_inner_model():
    print("This is a nested model")
```

### Class Methods

#### `get(key)`
**Type:** `async` class method  
**Parameters:** 
- `key` (str): The Redis key to retrieve  
**Returns:** `Self`  
**Raises:** `KeyNotFound` if key doesn't exist  
**Description:** Retrieves a model instance from Redis by its key.

```python
user = await User.get("User:abc-123")
```

#### `delete_by_key(key)`
**Type:** `async` class method  
**Parameters:** 
- `key` (str): The Redis key to delete  
**Returns:** `bool`  
**Description:** Deletes a model from Redis by its key without needing to load it first.

```python
success = await User.delete_by_key("User:abc-123")
```

#### `class_key_initials()`
**Type:** Class method  
**Returns:** `str`  
**Description:** Returns the class name used as the key prefix. Override to customize key naming.

```python
class User(AtomicRedisModel):
    @classmethod
    def class_key_initials(cls):
        return "USR"  # Keys will be "USR:pk" instead of "User:pk"
```

### Context Managers

#### `lock_from_key(key, action="default", save_at_end=False)`
**Type:** `async` context manager  
**Parameters:**
- `key` (str): Redis key to lock
- `action` (str): Lock action name for different operation types
- `save_at_end` (bool): Whether to save changes when context exits  
**Returns:** `AsyncGenerator[Self, None]`  
**Description:** Acquires an exclusive lock on the model and yields the loaded instance.

```python
async with User.lock_from_key("User:123", "profile_update", save_at_end=True) as user:
    user.name = "Updated Name"
    # Automatically saved when context exits
```

#### `lock(action="default", save_at_end=False)`
**Type:** `async` context manager  
**Parameters:**
- `action` (str): Lock action name
- `save_at_end` (bool): Whether to save changes when context exits  
**Returns:** `AsyncGenerator[Self, None]`  
**Description:** Acquires an exclusive lock on the current model instance.

```python
async with user.lock("settings_update", save_at_end=True) as locked_user:
    locked_user.settings = {"theme": "dark"}
```

#### `pipeline(ignore_if_deleted=False)`
**Type:** `async` context manager  
**Parameters:**
- `ignore_if_deleted` (bool): Continue if model was deleted during pipeline  
**Returns:** `AsyncGenerator[Self, None]`  
**Description:** Batches all operations into a Redis pipeline for atomic execution.

```python
async with user.pipeline() as pipeline_user:
    user.score += 100
    user.achievements.append("New Achievement")
    # All operations executed atomically
```

### Configuration

#### `Meta`
**Type:** `ClassVar[RedisConfig]`  
**Description:** Configuration class for Redis connection settings and model behavior.

```python
class User(AtomicRedisModel):
    name: str
    age: int
    
    class Meta:
        redis = redis_client
        ttl = 3600  # Expire after 1 hour
```

### Special Behaviors

#### Key Field Definition
Use `KeyAnnotation` to specify which field should be used as the primary key:

```python
from rapyer.fields import KeyAnnotation
from typing import Annotated

class User(AtomicRedisModel):
    username: Annotated[str, KeyAnnotation] 
    email: str
    
user = User(username="john_doe", email="john@example.com")
print(user.pk)   # "john_doe"
print(user.key)  # "User:john_doe"
```

#### Automatic Redis Type Conversion
Model fields are automatically converted to Redis-compatible types:

```python
class User(AtomicRedisModel):
    name: str          # Becomes RedisStr
    tags: List[str]    # Becomes RedisList[str]
    settings: Dict[str, str]  # Becomes RedisDict[str, str]
```

#### Field Linking
Redis type fields are automatically linked to their parent model for proper key resolution:

```python
user = User(name="John", tags=["python", "redis"])
print(user.tags.key)  # "User:abc-123.tags"
```

### Error Handling

#### `KeyNotFound`
Raised when attempting to get or load a model that doesn't exist in Redis:

```python
from rapyer.errors import KeyNotFound

try:
    user = await User.get("User:nonexistent")
except KeyNotFound:
    print("User not found in Redis")
```

### Example Usage

```python
from rapyer import AtomicRedisModel
from typing import List, Dict

class User(AtomicRedisModel):
    name: str
    email: str
    age: int = 0
    tags: List[str] = []
    settings: Dict[str, str] = {}

# Create and save
user = User(name="John", email="john@example.com", age=30)
await user.save()

# Retrieve
retrieved_user = await User.get(user.key)

# Update atomically
await user.aupdate(age=31, tags=["python", "redis"])

# Batch operations
async with user.pipeline():
    user.age += 1
    user.tags.append("asyncio")
    user.settings["theme"] = "dark"

# Lock for exclusive access
async with user.lock("profile_update", save_at_end=True):
    if user.age >= 25:
        user.tags.append("adult")
        user.settings["account_type"] = "premium"
```