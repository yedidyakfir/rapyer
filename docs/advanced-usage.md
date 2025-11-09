# Advanced Usage

This guide covers advanced features and patterns for experienced Rapyer users who need more control over their Redis models.

## Custom Primary Keys with Key Annotation

By default, Rapyer automatically generates primary keys for Redis storage using an internal `_pk` field. However, you can specify a custom field to act as the primary key using the `Key` annotation. This is useful when you have meaningful identifiers like user IDs, timestamps, or other unique values with special significance.

### Basic Usage

```python
from rapyer import AtomicRedisModel
from rapyer.fields import Key

class User(AtomicRedisModel):
    user_id: Key(str)  # This field will be used as the primary key
    name: str
    email: str
    age: int = 25

# The model will use user_id as the primary key
user = User(user_id="user123", name="John Doe", email="john@example.com")
await user.save()

# Access the primary key value
print(user.pk)  # "user123" (value of user_id field)
print(user.key) # "User:user123" (full Redis key)
```

### Alternative Annotation Syntax

You can also use the `Annotated` syntax for more complex type hints:

```python
from typing import Annotated
from datetime import datetime
from rapyer import AtomicRedisModel
from rapyer.fields import Key

class Event(AtomicRedisModel):
    created_at: Annotated[datetime, Key()]  # datetime as primary key
    event_name: str
    description: str
    duration_minutes: int = 60

# The model will use the datetime as the primary key
event = Event(
    created_at=datetime(2023, 12, 25, 10, 30, 45),
    event_name="Christmas Meeting",
    description="Annual holiday planning meeting"
)
await event.save()

print(event.pk)  # datetime(2023, 12, 25, 10, 30, 45)
```

### Use Cases for Custom Keys

#### Date/Time-Based Keys
Useful for time-series data or when you need chronological ordering:

```python
class LogEntry(AtomicRedisModel):
    timestamp: Key(datetime)
    level: str
    message: str
    source: str

log = LogEntry(
    timestamp=datetime.now(),
    level="ERROR", 
    message="Database connection failed",
    source="api.py"
)
```

#### Meaningful String IDs  
When you have external identifiers that should be preserved:

```python
class Product(AtomicRedisModel):
    sku: Key(str)  # Product SKU as primary key
    name: str
    price: float
    category: str

product = Product(
    sku="LAPTOP-123",
    name="Gaming Laptop",
    price=1299.99,
    category="Electronics"
)
```

#### Composite String Keys
For hierarchical or namespaced identifiers:

```python
class CacheEntry(AtomicRedisModel):
    cache_key: Key(str)  # Composite key like "user:123:session"
    data: dict
    expires_at: datetime

entry = CacheEntry(
    cache_key="user:456:preferences",
    data={"theme": "dark", "language": "en"},
    expires_at=datetime.now() + timedelta(hours=24)
)
```

### Important Considerations

#### When NOT to Use Custom Keys

⚠️ **Not recommended** for most use cases. The default auto-generated keys work well for typical applications.

Avoid custom keys when:
- You don't have a natural unique identifier
- The field value might change over time
- You're unsure about uniqueness guarantees
- Performance is critical (auto-generated keys are optimized)

#### When Custom Keys Are Useful

✅ **Recommended** for specific scenarios:

- **Date/Time keys**: For time-series data where chronological ordering matters
- **External IDs**: When integrating with existing systems that have established IDs  
- **Meaningful identifiers**: SKUs, UUIDs, or other business-relevant unique values
- **Special semantics**: When the key itself carries important meaning

#### Key Uniqueness

Ensure your custom key field values are unique:

```python
# Good: Guaranteed unique values
class User(AtomicRedisModel):
    email: Key(str)  # Emails are naturally unique
    name: str

# Risky: Non-unique values could cause conflicts  
class User(AtomicRedisModel):
    name: Key(str)    # Names might not be unique!
    email: str
```

#### Immutability

Custom key field values should not change after the model is saved:

```python
user = User(email="john@example.com", name="John")
await user.save()

# Avoid changing the key field value
user.email = "john.doe@example.com"  # This changes the primary key!
await user.save()  # This might create a new record instead of updating
```

### Performance Notes

- Custom keys have the same performance as auto-generated keys for storage and retrieval
- The key field is used directly in Redis operations
- No additional overhead is introduced by using custom keys

### Migration Considerations

If you need to add a custom key to an existing model:

1. **Data Migration**: Existing records will continue using auto-generated keys
2. **Backward Compatibility**: New records will use the custom key field
3. **Gradual Migration**: Consider migrating data in batches if needed

```python
# Before: Using auto-generated keys
class User(AtomicRedisModel):
    name: str
    email: str

# After: Adding custom key (existing records keep auto-generated keys)
class User(AtomicRedisModel):
    email: Key(str)  # New records will use email as key
    name: str
```

### Best Practices

1. **Choose Stable Values**: Use fields that won't change over the model's lifetime
2. **Ensure Uniqueness**: Verify that key field values are guaranteed to be unique
3. **Document Intent**: Clearly document why a custom key is necessary
4. **Test Thoroughly**: Ensure your application handles key-based operations correctly
5. **Consider Performance**: Evaluate whether custom keys improve or impact your use case

The `Key` annotation provides powerful flexibility for specialized use cases while maintaining Rapyer's atomic operation guarantees and type safety.