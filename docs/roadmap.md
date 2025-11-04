# Rapyer Roadmap

This is the current roadmap for the rayper package, note that this is just a basic POC.
You are welcome to add suggestions and contribute to our development.

## Enhanced Pipeline Support for All Types

**Current**: Only list and dict operations sync with Redis in pipeline mode
**Goal**: All Redis types support automatic pipeline synchronization

### Tasks
- [ ] **RedisInt**: Support `+=`, `-=`, `*=`, `/=` operators in pipeline
- [ ] **RedisStr**: Support `+=` (concatenation) in pipeline  
- [ ] **RedisBytes**: Support byte operations in a pipeline
- [ ] **RedisDateTime**: Support datetime modifications in pipeline
- [ ] **Testing**: Comprehensive tests for all pipeline operations

### Example Usage
```python
async with model.pipeline() as p:
    p.score += 10        # RedisInt - syncs to Redis
    p.name += " (Pro)"   # RedisStr - syncs to Redis  
    p.tags.append("new") # RedisList - already works
    # All changes applied atomically
```

**Benefits**: Complete atomic operation coverage, consistent developer experience across all types

## Bulk Operations Support

**Goal**: Enable efficient bulk insert, update, and delete operations for multiple models

### Tasks
- [ ] **Bulk Insert**: Create multiple models in a single Redis transaction
- [ ] **Bulk Update**: Update multiple models efficiently  
- [ ] **Bulk Delete**: Delete multiple models in one operation
- [ ] **Batch Loading**: Load multiple models by keys efficiently

### Example Usage
```python
# Bulk insert
users = [User(name=f"user{i}") for i in range(100)]
await User.bulk_insert(users)

# Bulk delete
await User.bulk_delete(["user:1", "user:2", "user:3"])

# Batch load
users = await User.bulk_get(["user:1", "user:2", "user:3"])
```

**Benefits**: Better performance for large datasets, reduced Redis round trips

## Complex Selection and Querying

**Goal**: Enable complex field-based queries using Python comparison operators

### Tasks
- [ ] **Field Comparisons**: Support `>`, `<`, `>=`, `<=`, `==`, `!=` operators on model fields
- [ ] **Logical Operators**: Support `&` (and), `|` (or), `~` (not) for complex queries
- [ ] **Query Builder**: Build Redis search queries from Python expressions
- [ ] **Index Management**: Automatic field indexing for query performance

### Example Usage
```python
# Simple field comparisons
adults = await User.find(User.age > 18).to_list()
active_users = await User.find(User.status == "active").to_list()

# Complex queries with logical operators
target_users = await User.find(
    (User.age > 25) & (User.score >= 100) & (User.active == True)
).to_list()

# Single result queries
admin = await User.find_one(User.role == "admin")
```

**Benefits**: Pythonic query syntax, improved developer experience, efficient Redis search

## Conditional Pipeline Actions

**Goal**: Enable complex conditional logic within pipeline operations

### Tasks
- [ ] **Conditional Execution**: Support `if_true()` and `else()` methods on field comparisons
- [ ] **Loop Operations**: Support iteration over collections in pipelines
- [ ] **Nested Conditions**: Allow chaining of conditional statements
- [ ] **Pipeline Context**: Maintain pipeline context through conditional blocks

### Example Usage
```python
async with user.pipeline() as p:
    # Simple conditional
    (p.age > 17).if_true(
        lambda: p.status.set("adult")
    ).else(
        lambda: p.status.set("minor")
    )
    
    # Complex conditional with multiple actions
    (p.score >= 100).if_true([
        lambda: p.level.set("premium"),
        lambda: p.badges.append("high_scorer"),
        lambda: p.notifications.update({"achievement": "unlocked"})
    ])
    
    # Loop operations
    for item in p.inventory:
        (item.expired).if_true(
            lambda: p.inventory.remove(item)
        )
```

**Benefits**: Advanced pipeline logic, reduced round trips, atomic conditional operations

## Field Access and Extraction Support

**Goal**: Enable extraction of specific fields from nested structures using dot notation

### Tasks
- [ ] **Nested Field Access**: Support `model.field_lst[0].field_int.get(redis_id)` syntax
- [ ] **Dynamic Field Extraction**: Allow runtime field path resolution
- [ ] **Type Safety**: Maintain type hints through nested access
- [ ] **Performance Optimization**: Efficient Redis operations for nested field access

### Example Usage
```python
# Extract specific nested field
value = await model.field_lst[0].field_int.get(redis_id)

# Multiple nested field extractions
values = await model.extract_fields([
    "field_lst[0].field_int",
    "field_lst[1].field_str", 
    "nested_dict.sub_field"
], redis_id)
```

**Benefits**: Simplified nested data access, improved developer experience, efficient field-specific operations

## Selective Field Updates in BaseModel

**Goal**: Enable direct field updates in Redis without loading the entire model, using an `aupdate()` method.
This way fields that are not redis-supported will be able to perform atomic actions like we can do on list and dict items (with aset_item)

### Tasks
- [ ] **aupdate() Method**: Implement `model.aupdate(field1="value", field2=123)` for selective field updates
- [ ] **Type Safety**: Maintain field type validation during updates
- [ ] **Redis Optimization**: Use Redis JSON path operations for efficient field-only updates
- [ ] **Class Field Access**: Support `model.aupdate(ModelClass.field1="value")` syntax for better IDE support
- [ ] **Atomic Updates**: Ensure all field updates in single aupdate call are atomic
- [ ] **Nested Field Updates**: Support updating nested model fields efficiently

### Example Usage
```python
# Basic field updates
await user.aupdate(name="John Doe", age=25)

# Using class field references for better IDE support
await user.aupdate(User.name="John Doe", User.age=25)

# Mixed syntax
await user.aupdate(name="John Doe", User.age=25)

# Nested field updates
await user.aupdate(profile__address__city="New York")
```

**Benefits**: Reduced Redis bandwidth, improved performance for partial updates, better developer experience for field-specific operations

## TTL Postponement on Model Usage

**Goal**: Allow postponing TTL expiration every time a model is accessed or used, preventing deletion while the model remains active

### Tasks
- [ ] **Usage-Based TTL**: Update TTL automatically when model is accessed or modified
- [ ] **Configurable Behavior**: Option to enable/disable TTL postponement per model class
- [ ] **TTL Refresh Strategy**: Define when and how TTL gets refreshed (read, write, or both)
- [ ] **Performance Optimization**: Efficient TTL updates without impacting model operations
- [ ] **Configuration Options**: Allow setting TTL refresh interval and grace periods

### Example Usage
```python
class User(AtomicRedisModel):
    name: str
    email: str
    
    class Config:
        ttl_postpone_on_access = True  # Refresh TTL on any access
        ttl_postpone_on_write = True   # Refresh TTL on writes only

# TTL gets postponed automatically
user = await User.get("user:123")  # TTL refreshed to another 3600 seconds
user.name = "Updated Name"          # TTL refreshed again
await user.save()
```

**Benefits**: Prevents premature deletion of active models, better cache behavior for frequently accessed data, configurable per-model basis