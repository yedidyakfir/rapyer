# Atomic Actions

Rapyer provides powerful atomic operations through context managers that ensure data consistency when performing multiple Redis operations. These operations guarantee that either all changes are applied together or none at all, preventing race conditions in concurrent environments.

## Available Context Managers

### 1. Lock Context Manager

The `lock()` context manager provides exclusive access to a Redis model instance, ensuring that only one process can modify the data at a time.

```python
from rapyer.base import BaseRedisModel


class User(BaseRedisModel):
    name: str
    score: int = 0
    metadata: dict[str, str] = {}


async def update_user_safely():
    user = await User.get("User:123")

    # Lock the user for exclusive access
    async with user.lock() as locked_user:
        # All operations within this block are performed exclusively
        locked_user.score += 10
        await locked_user.metadata.aupdate(last_modified="2024-01-01")
        # Changes are automatically saved when exiting the context
```

#### Lock with Custom Action

You can specify a custom action name to create different lock scopes for the same model:

```python
async with user.lock("score_update") as locked_user:
    locked_user.score += 100
    
# This can run concurrently with the above since it's a different action
async with user.lock("metadata_update") as locked_user:
    await locked_user.metadata.aupdate(region="us-east")
```

### 2. Lock from Key Context Manager

The `lock_from_key()` class method allows you to acquire a lock directly using a key without first retrieving the model instance.

```python
async def update_by_key():
    # Lock and get the model in one operation
    async with User.lock_from_key("User:123") as locked_user:
        locked_user.name = "Updated Name"
        await locked_user.metadata.aupdate(status="active")
        # Model is automatically saved when exiting the context
```

#### Lock from Key with Custom Action

```python
async with User.lock_from_key("User:123", "score_increment") as locked_user:
    locked_user.score += 1
```

### 3. Pipeline Context Manager

The `pipeline()` context manager batches multiple Redis operations and executes them atomically. Unlike locks, pipelines don't block other operations but ensure all operations within the pipeline are executed together.

```python
async def batch_operations():
    user = await User.get("User:123")
    
    async with user.pipeline() as pipe_user:
        # All these operations are batched and executed atomically
        await pipe_user.metadata.aupdate(
            last_login="2024-01-01",
            login_count="150"
        )
        await pipe_user.score.set(1000)
        await pipe_user.name.set("Premium User")
        
        # Operations are not applied to Redis yet
        # You can verify by loading the model again:
        current_user = await User.get("User:123")
        # current_user still has the old values
        
    # Now all operations are applied atomically to Redis
```

## Atomicity Guarantees

### Lock Context Managers

- **Exclusive Access**: Only one process can hold a lock for a specific model and action combination
- **Automatic Save**: Changes are automatically saved when exiting the context successfully
- **Exception Handling**: If an exception occurs within the context, changes are not saved
- **Deadlock Prevention**: Locks are automatically released when the context exits

### Pipeline Context Manager

- **Batch Execution**: All operations within the pipeline are executed together
- **Atomic Commitment**: Either all operations succeed or none are applied
- **Exception Rollback**: If an exception occurs, no operations are applied to Redis
- **Performance**: More efficient than individual operations for multiple changes

## Supported Operations in Pipeline

The following operations work within pipeline context:

### List Operations
- `aappend()` - Add single item
- `aextend()` - Add multiple items
- `ainsert()` - Insert at specific position
- `aclear()` - Clear all items

### Dictionary Operations
- `aset_item()` - Set single key-value pair
- `aupdate()` - Update multiple key-value pairs
- `adel_item()` - Delete single key
- `aclear()` - Clear all items

### Basic Field Operations
- `set()` - Set field value

### Model Operations
- `delete()` - Delete the entire model
- `try_delete()` - Attempt to delete (returns boolean)

## Limitations

### Operations Not Supported in Pipeline

Some operations require immediate response from Redis and cannot be used within pipelines:

```python
# These operations will raise exceptions in pipeline context:
async with user.pipeline() as pipe_user:
    # ❌ These don't work in pipelines:
    item = await pipe_user.tags.apop()  # Requires return value
    key, value = await pipe_user.metadata.apopitem()  # Requires return value
    value = await pipe_user.metadata.apop("key")  # Requires return value
```

### Nested Model Restrictions

Atomic operations can only be initiated from base Redis models (top-level models), not from nested models:

```python
class Address(BaseRedisModel):
    street: str
    city: str

class User(BaseRedisModel):
    name: str
    address: Address

user = User(name="John", address=Address(street="123 Main", city="NYC"))

# ✅ This works - from base model
async with user.lock() as locked_user:
    locked_user.name = "Jane"

# ❌ This will raise RuntimeError - from nested model
async with user.address.lock() as locked_address:  # RuntimeError!
    locked_address.city = "Boston"
```

## Best Practices

### Choose the Right Context Manager

- **Use `lock()`** when you need exclusive access and want to prevent concurrent modifications
- **Use `pipeline()`** when you want to batch multiple operations for better performance and atomicity
- **Use `lock_from_key()`** when you need to lock a model by key without first loading it

### Error Handling

```python
try:
    async with user.lock() as locked_user:
        # Perform operations
        locked_user.score += 10
        # If an exception occurs here, changes won't be saved
        if locked_user.score > 1000:
            raise ValueError("Score too high")
except ValueError:
    # Handle the exception
    print("Operation failed, no changes were saved")
```

### Performance Considerations

```python
# ❌ Inefficient - multiple Redis roundtrips
await user.metadata.aupdate(key1="value1")
await user.metadata.aupdate(key2="value2") 
await user.score.set(100)

# ✅ Efficient - single atomic operation
async with user.pipeline() as pipe_user:
    await pipe_user.metadata.aupdate(key1="value1", key2="value2")
    await pipe_user.score.set(100)
```

### Concurrent Safety

```python
# Multiple processes can safely increment the same counter
async def increment_counter(user_id: str):
    async with User.lock_from_key(f"User:{user_id}", "counter") as locked_user:
        locked_user.score += 1
```

## Examples

### Safe Counter Implementation

```python
class Counter(BaseRedisModel):
    value: int = 0
    
async def increment_counter(counter_id: str, amount: int = 1):
    async with Counter.lock_from_key(f"Counter:{counter_id}") as counter:
        counter.value += amount
    return counter.value
```

### Batch User Profile Update

```python
async def update_user_profile(user_id: str, profile_data: dict):
    async with User.lock_from_key(f"User:{user_id}") as user:
        async with user.pipeline() as pipe_user:
            await pipe_user.metadata.aupdate(**profile_data)
            await pipe_user.metadata.aset_item("last_updated", "2024-01-01")
            # All updates applied atomically
```

### Complex Transaction

```python
async def transfer_points(from_user_id: str, to_user_id: str, points: int):
    # Lock both users to prevent race conditions
    async with User.lock_from_key(f"User:{from_user_id}", "transfer") as from_user:
        async with User.lock_from_key(f"User:{to_user_id}", "transfer") as to_user:
            if from_user.score < points:
                raise ValueError("Insufficient points")
            
            from_user.score -= points
            to_user.score += points
            # Both changes saved automatically when contexts exit
```