# Working with Nested Models

RedisPydantic automatically supports nested Pydantic models by converting regular `BaseModel` classes into Redis-enabled versions. This allows you to use all Redis field operations on nested model fields.

## Basic Nested Models

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

## Deep Nesting Support

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

## Nested Model Persistence

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

## Working with Nested Types

```python
class User(BaseRedisModel):
    preferences: Dict[str, List[str]] = {}
    scores: List[int] = []

user = User()

# Nested operations
await user.preferences.aset_item("languages", ["python", "rust"])
await user.scores.aextend([95, 87, 92])
```

## Nested Model Duplication

Duplication works seamlessly with nested models:

```python
class UserProfile(BaseModel):
    bio: str = ""
    skills: List[str] = Field(default_factory=list)
    preferences: Dict[str, str] = Field(default_factory=dict)

class User(BaseRedisModel):
    name: str
    profile: UserProfile = Field(default_factory=UserProfile)
    tags: List[str] = Field(default_factory=list)

# Create user with nested data
original = User(
    name="Alice",
    profile=UserProfile(
        bio="Software Engineer",
        skills=["Python", "Redis"],
        preferences={"theme": "dark", "lang": "en"}
    ),
    tags=["engineer", "python"]
)
await original.save()

# Duplicate preserves all nested structure
duplicate = await original.duplicate()

# Verify nested data is identical
assert duplicate.profile.bio == original.profile.bio
assert duplicate.profile.skills == original.profile.skills
assert duplicate.profile.preferences == original.profile.preferences

# Nested Redis operations work independently
await duplicate.profile.skills.aappend("JavaScript")
await original.profile.skills.load()
assert "JavaScript" not in original.profile.skills  # Original unchanged
assert "JavaScript" in duplicate.profile.skills      # Duplicate modified
```

## Nested Redis Models

When using `BaseRedisModel` as nested models, duplication preserves the Redis functionality:

```python
class UserStats(BaseRedisModel):
    login_count: int = 0
    preferences: Dict[str, bool] = Field(default_factory=dict)

class User(BaseRedisModel):
    name: str
    stats: UserStats = Field(default_factory=UserStats)

original = User(name="Bob")
await original.save()

# Add some stats data
await original.stats.preferences.aupdate(notifications=True, dark_mode=False)
original.stats.login_count = 10
await original.save()

# Duplicate preserves Redis nested model
duplicate = await original.duplicate()

# Independent Redis operations on nested models
await duplicate.stats.preferences.aset_item("email_alerts", True)
await original.stats.preferences.load()

assert "email_alerts" not in original.stats.preferences
assert duplicate.stats.preferences["email_alerts"] is True
```

## Duplication Restrictions

Duplication can only be performed on top-level models:

```python
user = User(name="Test")
await user.save()

# ✅ This works - duplicating top-level model
duplicate = await user.duplicate()

# ❌ This raises RuntimeError - cannot duplicate inner models
try:
    await user.profile.duplicate()  # Inner BaseModel
except RuntimeError as e:
    print(e)  # "Can only duplicate from top level model"

try:
    await user.stats.duplicate()    # Inner BaseRedisModel
except RuntimeError as e:
    print(e)  # "Can only duplicate from top level model"
```