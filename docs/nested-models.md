# Nested Models

Rapyer supports complex nested model structures where any inner model can use the same Redis actions as the upper model. This allows you to build sophisticated data hierarchies while maintaining full atomic operation support throughout the entire structure.

## Understanding Nested Models

Nested models in Rapyer maintain the same powerful Redis functionality at every level of nesting. Whether you have a simple nested model or a deeply complex hierarchy, all atomic operations remain available.

### Basic Nested Structure

```python
from rapyer import AtomicRedisModel
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class ContactInfo(BaseModel):
    email: str
    phone: str
    emergency_contact: str = ""

class UserProfile(AtomicRedisModel):
    user_id: str
    addresses: List[Address] = []
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    preferences: Dict[str, str] = {}
    tags: List[str] = []

# The nested models automatically inherit Redis functionality
user = UserProfile(
    user_id="user123",
    contact_info=ContactInfo(email="john@example.com", phone="555-1234")
)
await user.save()

# All Redis operations work on nested structures
await user.addresses.aappend(Address(
    street="123 Main St",
    city="Boston", 
    country="USA",
    postal_code="02101"
))
```

## Redis-Enabled Nested Models

For maximum functionality, you can create nested models that also inherit from `AtomicRedisModel`:

```python
class UserSettings(AtomicRedisModel):
    theme: str = "light"
    notifications: Dict[str, bool] = {}
    dashboard_config: List[str] = []

class UserStats(AtomicRedisModel):
    login_count: int = 0
    last_activity: datetime = None
    feature_usage: Dict[str, int] = {}

class AdvancedUser(AtomicRedisModel):
    username: str
    email: str
    settings: UserSettings = Field(default_factory=UserSettings)
    stats: UserStats = Field(default_factory=UserStats)
    tags: List[str] = []

# Create user with nested Redis models
user = AdvancedUser(username="johndoe", email="john@example.com")
await user.save()

# Nested Redis models have full atomic operation support
await user.settings.notifications.aupdate(
    email_alerts=True,
    push_notifications=False,
    weekly_summary=True
)

await user.stats.feature_usage.aupdate(
    dashboard_views=5,
    profile_edits=2,
    settings_changes=1
)

await user.settings.dashboard_config.aextend([
    "weather_widget",
    "news_feed", 
    "calendar"
])
```

## Complex Nested Hierarchies

Rapyer supports arbitrarily deep nesting with full functionality preserved:

```python
class ProjectTask(AtomicRedisModel):
    title: str
    status: str = "pending"
    tags: List[str] = []
    metadata: Dict[str, str] = {}

class ProjectSection(AtomicRedisModel):
    name: str
    description: str = ""
    tasks: List[ProjectTask] = []
    section_tags: List[str] = []

class Project(AtomicRedisModel):
    name: str
    description: str
    sections: List[ProjectSection] = []
    collaborators: List[str] = []
    project_metadata: Dict[str, str] = {}

# Create complex nested structure
project = Project(
    name="Website Redesign",
    description="Complete overhaul of company website"
)
await project.save()

# Add a section with tasks
frontend_section = ProjectSection(
    name="Frontend Development",
    description="UI/UX implementation"
)

# Add tasks to the section
task1 = ProjectTask(title="Create wireframes")
task2 = ProjectTask(title="Implement responsive design")

await frontend_section.tasks.aextend([task1, task2])
await project.sections.aappend(frontend_section)

# Work with deeply nested data
await project.sections[0].tasks[0].tags.aappend("high-priority")
await project.sections[0].tasks[0].metadata.aupdate(
    assigned_to="designer@company.com",
    due_date="2024-02-15"
)
```

## Atomic Operations on Nested Models

All atomic operations work seamlessly with nested structures:

### List Operations in Nested Models

```python
class BlogPost(AtomicRedisModel):
    title: str
    content: str
    tags: List[str] = []
    comments: List[Dict[str, str]] = []

class Author(AtomicRedisModel):
    name: str
    email: str
    posts: List[BlogPost] = []
    author_tags: List[str] = []

author = Author(name="Jane Smith", email="jane@example.com")
await author.save()

# Create a new blog post
new_post = BlogPost(
    title="Getting Started with Rapyer",
    content="Rapyer is a powerful Redis ORM..."
)

# Add atomic operations to nested blog post
await new_post.tags.aextend(["redis", "python", "orm"])
await new_post.comments.aappend({
    "author": "reader1",
    "comment": "Great article!",
    "timestamp": str(datetime.now())
})

# Add the post to author's posts
await author.posts.aappend(new_post)
await author.author_tags.aappend("prolific_writer")
```

### Dictionary Operations in Nested Models

```python
class GameCharacter(AtomicRedisModel):
    name: str
    level: int = 1
    attributes: Dict[str, int] = {}
    inventory: Dict[str, int] = {}

class Guild(AtomicRedisModel):
    name: str
    description: str
    members: List[GameCharacter] = []
    guild_resources: Dict[str, int] = {}

guild = Guild(name="Dragon Slayers", description="Elite gaming guild")
await guild.save()

# Create character with nested atomic operations
character = GameCharacter(name="Warrior123")
await character.attributes.aupdate(
    strength=15,
    dexterity=12,
    intelligence=8
)

await character.inventory.aupdate(
    sword=1,
    shield=1,
    health_potion=5
)

# Add character to guild
await guild.members.aappend(character)

# Update guild resources atomically
await guild.guild_resources.aupdate(
    gold=1000,
    gems=50,
    experience_boost=3
)
```

## Pipeline Operations with Nested Models

Pipelines work with nested models for complex atomic transactions:

```python
class OrderItem(AtomicRedisModel):
    product_id: str
    quantity: int
    price: int  # in cents
    item_metadata: Dict[str, str] = {}

class Order(AtomicRedisModel):
    customer_id: str
    items: List[OrderItem] = []
    order_metadata: Dict[str, str] = {}
    total_amount: int = 0
    status: str = "pending"

async def process_order_with_items(order: Order, items_data: List[dict]):
    # Complex atomic transaction involving nested models
    async with order.pipeline() as pipelined_order:
        total = 0
        
        for item_data in items_data:
            # Create order item
            item = OrderItem(
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price=item_data["price"]
            )
            
            # Add metadata to nested item
            await item.item_metadata.aupdate(
                added_at=str(datetime.now()),
                source="web_order"
            )
            
            # Add item to order
            await pipelined_order.items.aappend(item)
            total += item.price * item.quantity
        
        # Update order totals and metadata
        order.total_amount = total
        await pipelined_order.total_amount.save()
        await pipelined_order.order_metadata.aupdate(
            processed_at=str(datetime.now()),
            item_count=str(len(items_data))
        )
        order.status = "confirmed"
        await pipelined_order.status.save()
    
    print(f"Order processed with {len(items_data)} items, total: ${total/100:.2f}")
```

## Lock Operations with Nested Models

Locks work across the entire nested structure:

```python
class UserAccount(AtomicRedisModel):
    username: str
    balance: int = 0
    transaction_history: List[Dict[str, str]] = []

class UserProfile(AtomicRedisModel):
    user_id: str
    account: UserAccount = Field(default_factory=UserAccount)
    preferences: Dict[str, str] = {}

async def transfer_funds(from_user_key: str, to_user_key: str, amount: int):
    # Lock both users for atomic fund transfer
    async with UserProfile.lock_from_key(from_user_key, "transfer") as from_user:
        async with UserProfile.lock_from_key(to_user_key, "transfer") as to_user:
            
            if from_user.account.balance >= amount:
                # Deduct from sender
                from_user.account.balance -= amount
                await from_user.account.transaction_history.aappend({
                    "type": "transfer_out",
                    "amount": str(amount),
                    "to": to_user.user_id,
                    "timestamp": str(datetime.now())
                })
                
                # Add to receiver
                to_user.account.balance += amount
                await to_user.account.transaction_history.aappend({
                    "type": "transfer_in",
                    "amount": str(amount),
                    "from": from_user.user_id,
                    "timestamp": str(datetime.now())
                })
                
                return True
            else:
                return False
```

## Working with Mixed Model Types

You can mix regular Pydantic models with AtomicRedisModel for flexibility:

```python
# Regular Pydantic model (no Redis operations)
class BasicAddress(BaseModel):
    street: str
    city: str

# Redis-enabled model (full atomic operations)
class ExtendedAddress(AtomicRedisModel):
    street: str
    city: str
    metadata: Dict[str, str] = {}
    tags: List[str] = []

class Company(AtomicRedisModel):
    name: str
    # Regular Pydantic model - automatically serialized
    headquarters: BasicAddress
    # Redis-enabled model - full atomic operations available
    branch_offices: List[ExtendedAddress] = []
    company_metadata: Dict[str, str] = {}

company = Company(
    name="Tech Corp",
    headquarters=BasicAddress(street="123 Main St", city="Boston")
)
await company.save()

# Regular model is serialized but no atomic operations
# company.headquarters.street = "456 Oak Ave"  # Regular assignment

# Redis-enabled nested model has full atomic operations
branch = ExtendedAddress(street="789 Pine St", city="San Francisco")
await branch.metadata.aupdate(
    opened_date="2024-01-01",
    office_type="regional"
)
await branch.tags.aextend(["west_coast", "tech_hub"])

await company.branch_offices.aappend(branch)
```

## Performance Considerations

### Nested Model Efficiency

```python
# ✅ Efficient - batch nested operations
async with user.pipeline() as pipelined_user:
    await pipelined_user.settings.notifications.aupdate(email=True, sms=False)
    user.stats.login_count += 1
    await pipelined_user.stats.login_count.save()
    await pipelined_user.tags.aappend("active_user")

# ❌ Less efficient - multiple individual operations
await user.settings.notifications.aupdate(email=True)
await user.settings.notifications.aupdate(sms=False)
user.stats.login_count += 1
await user.stats.login_count.save()
await user.tags.aappend("active_user")
```

### Memory Considerations

```python
# For large nested structures, consider loading specific parts
class LargeDataset(AtomicRedisModel):
    name: str
    metadata: Dict[str, str] = {}
    large_data: List[Dict[str, Any]] = []  # Could be very large

# Load only what you need
dataset = await LargeDataset.get("LargeDataset:123")
await dataset.metadata.load()  # Load only metadata
# dataset.large_data remains unloaded until explicitly loaded
```

## Error Handling in Nested Structures

```python
class ComplexOrder(AtomicRedisModel):
    customer_id: str
    items: List[OrderItem] = []
    shipping_info: Dict[str, str] = {}
    status: str = "draft"

async def create_complex_order(customer_id: str, order_data: dict):
    order = ComplexOrder(customer_id=customer_id)
    await order.save()
    
    try:
        async with order.pipeline() as pipelined_order:
            # Add items
            for item_data in order_data["items"]:
                item = OrderItem(**item_data)
                await pipelined_order.items.aappend(item)
            
            # Add shipping info
            await pipelined_order.shipping_info.aupdate(**order_data["shipping"])
            
            # Set status
            order.status = "confirmed"
            await pipelined_order.status.save()
            
        print("Order created successfully")
        return order
        
    except Exception as e:
        # If anything fails, the entire transaction is rolled back
        print(f"Order creation failed: {e}")
        await order.delete()  # Clean up
        raise
```

## Best Practices for Nested Models

### 1. Choose the Right Nesting Level

```python
# ✅ Good - logical grouping
class User(AtomicRedisModel):
    username: str
    profile: UserProfile  # Related data grouped together
    settings: UserSettings  # Settings grouped separately

# ❌ Avoid - too flat
class User(AtomicRedisModel):
    username: str
    profile_bio: str
    profile_avatar: str
    settings_theme: str
    settings_notifications: bool
    # ... many individual fields
```

### 2. Use Pipelines for Related Operations

```python
# ✅ Good - batch related nested operations
async with user.pipeline() as pipelined_user:
    user.profile.bio = "Updated bio"
    await pipelined_user.profile.bio.save()
    await pipelined_user.profile.tags.aappend("updated")
    user.settings.last_profile_update = datetime.now()
    await pipelined_user.settings.last_profile_update.save()
```

### 3. Lock at the Appropriate Level

```python
# ✅ Good - lock at user level for related changes
async with user.lock("profile_update") as locked_user:
    locked_user.profile.bio = "New bio"
    await locked_user.profile.tags.aappend("verified")
    locked_user.settings.last_update = datetime.now()
    await locked_user.settings.last_update.save()
```

## Complete Example: Social Media Platform

```python
class Post(AtomicRedisModel):
    content: str
    author_id: str
    likes: List[str] = []  # user IDs who liked
    comments: List[Dict[str, str]] = []
    tags: List[str] = []
    metadata: Dict[str, str] = {}

class UserProfile(AtomicRedisModel):
    user_id: str
    display_name: str
    bio: str = ""
    follower_count: int = 0
    following_count: int = 0

class SocialUser(AtomicRedisModel):
    username: str
    email: str
    profile: UserProfile = Field(default_factory=UserProfile)
    posts: List[Post] = []
    activity_log: List[Dict[str, str]] = []

async def create_post_with_engagement(user: SocialUser, content: str, tags: List[str]):
    # Create post with atomic operations on nested structure
    post = Post(content=content, author_id=user.username)
    
    async with post.pipeline() as pipelined_post:
        await pipelined_post.tags.aextend(tags)
        await pipelined_post.metadata.aupdate(
            created_at=str(datetime.now()),
            platform="web"
        )
    
    # Add post to user and update activity atomically
    async with user.pipeline() as pipelined_user:
        await pipelined_user.posts.aappend(post)
        await pipelined_user.activity_log.aappend({
            "action": "post_created",
            "post_id": post.pk,
            "timestamp": str(datetime.now())
        })
    
    return post

async def like_post(user: SocialUser, post: Post):
    # Atomic like operation affecting multiple nested structures
    async with post.lock("engagement") as locked_post:
        if user.username not in locked_post.likes:
            async with locked_post.pipeline() as pipelined_post:
                await pipelined_post.likes.aappend(user.username)
                await pipelined_post.metadata.aupdate(
                    last_interaction=str(datetime.now())
                )
            
            # Update user activity
            await user.activity_log.aappend({
                "action": "liked_post",
                "post_id": post.pk,
                "timestamp": str(datetime.now())
            })
            
            return True
    return False
```

This comprehensive example shows how Rapyer's nested models maintain full Redis functionality at every level, enabling complex social media operations while ensuring data consistency and atomic behavior throughout the entire structure.

## Summary

Rapyer's nested models provide:

- **Full Redis functionality** at every nesting level
- **Atomic operations** that work seamlessly with complex hierarchies  
- **Pipeline support** for efficient batch operations on nested data
- **Lock mechanisms** that protect entire nested structures
- **Flexible mixing** of regular Pydantic models with Redis-enabled models
- **Performance optimization** through intelligent operation batching

Whether you're building simple nested configurations or complex multi-level data structures, Rapyer ensures that all atomic operations remain available and performant throughout your entire model hierarchy.