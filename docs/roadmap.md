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