# CRUD Operations

After defining your model, you'll need to perform basic CRUD (Create, Read, Update, Delete) operations with Redis. This page covers how to save, retrieve, and delete model instances.

## Saving Models

Use the `save()` method to store your model instance in Redis:

```python
import asyncio
from rapyer import AtomicRedisModel
from typing import List, Dict

class User(AtomicRedisModel):
    name: str
    age: int
    email: str
    tags: List[str] = []
    preferences: Dict[str, str] = {}

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

if __name__ == "__main__":
    asyncio.run(main())
```

## Retrieving Models

Use the `get()` class method to load model instances from Redis:

```python
async def main():
    # Create and save a user
    user = User(name="Bob", age=30, email="bob@example.com")
    await user.save()
    user_key = user.key
    
    # Retrieve the user by key
    loaded_user = await User.get(user_key)
    print(f"Loaded user: {loaded_user.name}, Age: {loaded_user.age}")
    
    # Handle non-existent keys
    missing_user = await User.get("non-existent-key")
    if missing_user is None:
        print("User not found")

if __name__ == "__main__":
    asyncio.run(main())
```

## Updating Models

There are several ways to update model data:

### Full Model Update

Modify the model instance and save again:

```python
async def main():
    # Create and save user
    user = User(name="Charlie", age=28, email="charlie@example.com")
    await user.save()
    
    # Update and save
    user.age = 29
    user.email = "charlie.new@example.com"
    await user.save()
    
    # Verify the update
    updated_user = await User.get(user.key)
    print(f"Updated age: {updated_user.age}, email: {updated_user.email}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Field-Level Atomic Updates

For better performance and atomicity, update specific fields:

```python
async def main():
    user = User(name="David", age=35, tags=["manager"], preferences={"theme": "dark"})
    await user.save()
    
    # Atomic field updates
    user.age = 36
    await user.age.asave()  # Save only the age field
    
    # Atomic collection operations
    await user.tags.aappend("leader")
    await user.preferences.aupdate(language="fr")
    
    # Verify updates
    updated_user = await User.get(user.key)
    print(f"Updated user: {updated_user.name}, Age: {updated_user.age}")
    print(f"Tags: {updated_user.tags}, Preferences: {updated_user.preferences}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Deleting Models

Remove model instances from Redis using the `delete()` method:

```python
async def main():
    # Create and save user
    user = User(name="Eve", age=22, email="eve@example.com")
    await user.save()
    user_key = user.key
    
    # Delete from Redis
    await user.delete()
    print(f"Deleted user with key: {user_key}")
    
    # Verify deletion
    deleted_user = await User.get(user_key)
    if deleted_user is None:
        print("User successfully deleted")

if __name__ == "__main__":
    asyncio.run(main())
```

## Checking Existence

Check if a model exists in Redis without loading it:

```python
async def main():
    user = User(name="Frank", age=40, email="frank@example.com")
    await user.save()
    
    # Check if user exists
    exists = await User.exists(user.key)
    print(f"User exists: {exists}")
    
    # Delete and check again
    await user.delete()
    exists_after_delete = await User.exists(user.key)
    print(f"User exists after delete: {exists_after_delete}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Complete CRUD Example

Here's a comprehensive example showing all CRUD operations:

```python
import asyncio
import redis.asyncio as redis
from rapyer import AtomicRedisModel
from typing import List, Dict

class User(AtomicRedisModel):
    name: str
    age: int
    email: str
    tags: List[str] = []
    preferences: Dict[str, str] = {}

async def crud_example():
    # Setup Redis connection
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )
    User.Meta.redis = redis_client
    User.Meta.ttl = 3600  # 1 hour TTL
    
    # CREATE
    user = User(
        name="John Doe",
        age=30,
        email="john@example.com",
        tags=["developer", "python"],
        preferences={"theme": "dark", "notifications": "enabled"}
    )
    await user.save()
    print(f"Created user: {user.key}")
    
    # READ
    loaded_user = await User.get(user.key)
    print(f"Retrieved: {loaded_user.name}, {loaded_user.age}")
    
    # UPDATE
    loaded_user.age = 31
    await loaded_user.tags.aappend("redis")
    await loaded_user.preferences.aupdate(theme="light")
    await loaded_user.save()
    print("Updated user")
    
    # Verify update
    updated_user = await User.get(user.key)
    print(f"After update: Age={updated_user.age}, Tags={updated_user.tags}")
    
    # DELETE
    await updated_user.delete()
    print("Deleted user")
    
    # Verify deletion
    deleted_user = await User.get(user.key)
    print(f"After deletion: {deleted_user}")  # Should be None

if __name__ == "__main__":
    asyncio.run(crud_example())
```

This covers all the essential CRUD operations you'll need when working with Rapyer models in Redis.