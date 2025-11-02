# Basic Operations

Learn the fundamental operations for working with Rapyer models: saving, loading, retrieving, and deleting data.

## Model Definition

First, define your model by inheriting from `AtomicRedisModel`:

```python
from rapyer.base import AtomicRedisModel
from typing import List, Dict
from datetime import datetime

class User(AtomicRedisModel):
    name: str
    age: int
    email: str
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    created_at: datetime
    is_active: bool = True
```

## Save Operation

The `save()` method stores your model in Redis. It can only be called from top-level models (not nested models).

### Basic Save

```python
import asyncio
from datetime import datetime

async def save_user():
    user = User(
        name="John Doe",
        age=30,
        email="john@example.com",
        created_at=datetime.now()
    )
    
    # Save to Redis
    await user.save()
    print(f"User saved with key: {user.key}")
    # Output: User saved with key: User:550e8400-e29b-41d4-a716-446655440000

asyncio.run(save_user())
```

### Save with TTL (Time To Live)

Configure automatic expiration:

```python
class Session(AtomicRedisModel):
    user_id: str
    token: str
    
    class Meta:
        redis = redis_client
        ttl = 3600  # Expire after 1 hour

async def save_session():
    session = Session(user_id="user123", token="abc123")
    await session.save()  # Will expire automatically after 1 hour
```

## Get Operation

Retrieve models from Redis using their key.

### Get by Key

```python
async def get_user():
    # Get user by full key
    user_key = "User:550e8400-e29b-41d4-a716-446655440000"
    user = await User.get(user_key)
    
    print(f"Retrieved user: {user.name}, age: {user.age}")
    return user
```

### Error Handling

```python
from rapyer.errors.base import KeyNotFound

async def safe_get_user(user_key: str):
    try:
        user = await User.get(user_key)
        return user
    except KeyNotFound:
        print(f"User with key {user_key} not found")
        return None
```

## Load Operation

Load specific fields or all fields from Redis without recreating the model.

### Load All Fields

```python
async def load_user_data():
    # Create user instance with known key
    user = User(name="", age=0, email="", created_at=datetime.now())
    user.pk = "550e8400-e29b-41d4-a716-446655440000"
    
    # Load all data from Redis
    await user.load()
    print(f"Loaded user: {user.name}")
```

### Load Specific Fields

```python
async def load_specific_fields():
    user = User(name="", age=0, email="", created_at=datetime.now())
    user.pk = "550e8400-e29b-41d4-a716-446655440000"
    
    # Load only specific fields
    await user.name.load()
    await user.email.load()
    
    print(f"Name: {user.name}, Email: {user.email}")
    # age and other fields remain unloaded
```

## Delete Operations

Remove data from Redis.

### Delete Model Instance

```python
async def delete_user():
    user = await User.get("User:550e8400-e29b-41d4-a716-446655440000")
    
    # Delete the user
    deleted_count = await user.delete()
    print(f"Deleted {deleted_count} keys")  # Returns 1 if successful
```

### Delete by Key (Class Method)

```python
async def delete_by_key():
    user_key = "User:550e8400-e29b-41d4-a716-446655440000"
    
    # Try to delete - returns True if key existed and was deleted
    was_deleted = await User.try_delete(user_key)
    
    if was_deleted:
        print("User deleted successfully")
    else:
        print("User key not found")
```

## Duplicate Operations

Create copies of existing models.

### Duplicate Single Model

```python
async def duplicate_user():
    original_user = await User.get("User:550e8400-e29b-41d4-a716-446655440000")
    
    # Create a duplicate with new UUID
    duplicate = await original_user.duplicate()
    
    print(f"Original key: {original_user.key}")
    print(f"Duplicate key: {duplicate.key}")
    
    # Both models exist independently in Redis
```

### Duplicate Many Models

```python
async def create_test_users():
    template_user = User(
        name="Test User",
        age=25,
        email="test@example.com",
        created_at=datetime.now()
    )
    await template_user.save()
    
    # Create 5 duplicates
    duplicates = await template_user.duplicate_many(5)
    
    print(f"Created {len(duplicates)} duplicate users")
    for i, user in enumerate(duplicates):
        print(f"User {i+1}: {user.key}")
```

## Key Management

Understanding and working with model keys.

### Understanding Keys

```python
async def key_examples():
    user = User(name="John", age=30, email="john@example.com", created_at=datetime.now())
    
    # Key components
    print(f"Primary key (UUID): {user.pk}")
    print(f"Full Redis key: {user.key}")
    print(f"Key format: {user.key_initials}:{user.pk}")
    
    # Custom key prefixes
    user.pk = "custom-user-id"  # Set custom primary key
    print(f"Custom key: {user.key}")
```

### Key Only Operations

```python
async def key_only_operations():
    # Delete without loading the model
    user_key = "User:550e8400-e29b-41d4-a716-446655440000"
    await User.try_delete(user_key)
    
    # Check if key exists (by trying to get it)
    try:
        await User.get(user_key)
        print("User exists")
    except KeyNotFound:
        print("User does not exist")
```

## Complete Example

Here's a complete example demonstrating all basic operations:

```python
import asyncio
from datetime import datetime
from rapyer.base import AtomicRedisModel
from rapyer.errors.base import KeyNotFound

class BlogPost(AtomicRedisModel):
    title: str
    content: str
    author: str
    tags: List[str] = []
    view_count: int = 0
    published_at: datetime
    
    class Meta:
        redis = redis_client  # Your Redis client

async def blog_post_lifecycle():
    # 1. Create and save
    post = BlogPost(
        title="Getting Started with Rapyer",
        content="Rapyer is an awesome Redis ORM...",
        author="John Doe",
        tags=["redis", "python", "orm"],
        published_at=datetime.now()
    )
    await post.save()
    print(f"✅ Post saved: {post.key}")
    
    # 2. Retrieve
    retrieved_post = await BlogPost.get(post.key)
    print(f"✅ Post retrieved: {retrieved_post.title}")
    
    # 3. Update fields
    retrieved_post.view_count = 100
    await retrieved_post.view_count.save()
    await retrieved_post.tags.aappend("tutorial")
    print("✅ Post updated")
    
    # 4. Load latest data
    await post.load()  # Refresh local instance
    print(f"✅ View count: {post.view_count}, Tags: {post.tags}")
    
    # 5. Duplicate
    duplicate_post = await post.duplicate()
    duplicate_post.title = "Copy of " + duplicate_post.title
    await duplicate_post.save()
    print(f"✅ Duplicate created: {duplicate_post.key}")
    
    # 6. Delete
    await post.delete()
    await duplicate_post.delete()
    print("✅ Posts deleted")

if __name__ == "__main__":
    asyncio.run(blog_post_lifecycle())
```

## Best Practices

### 1. Always Use Async/Await

```python
# ✅ Correct
await user.save()
await User.get(key)

# ❌ Incorrect - will not work
user.save()
User.get(key)
```

### 2. Handle Exceptions

```python
# ✅ Robust
try:
    user = await User.get(user_key)
except KeyNotFound:
    # Handle missing user
    user = None
```

### 3. Use Meaningful Primary Keys

```python
# ✅ Custom meaningful key
user = User(name="John", age=30, email="john@example.com", created_at=datetime.now())
user.pk = f"user_{user.email.replace('@', '_')}"
await user.save()
# Key: User:user_john_example_com
```

### 4. Top-Level Operations Only

```python
# ✅ Correct - operate on top-level models
await user.save()
await user.delete()

# ❌ Incorrect - nested models cannot be saved directly
# await user.profile.save()  # Will raise RuntimeError
```

## Next Steps

Now that you understand basic operations, explore:

- **[Supported Types](supported-types.md)** - All supported data types and their atomic operations
- **[Atomic Actions](atomic-actions.md)** - Advanced concurrency features and pipeline operations
- **[Nested Models](nested-models.md)** - Working with complex nested structures