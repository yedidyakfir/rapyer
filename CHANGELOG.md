# Changelog

## [1.0.2] - 2025-11-05

### ✨ Added

- **Inheritance Model Support**: Added support for inheritance models - models that inherit from a Redis model still create a Redis model with full functionality
- **Global Configuration**: Added `init_rapyer()` function to set Redis client and TTL for all models at once
  - Accepts Redis client instance or connection string (e.g., `"redis://localhost:6379"`)
  - Allows setting global TTL for all Redis models
  - Example: `init_rapyer(redis="redis://localhost:6379", ttl=3600)`
- **Atomic Updates**: Added `aupdate()` method to AtomicRedisModel for selective field updates without loading the entire model
  - Enables direct field updates in Redis: `await model.aupdate(field1="value", field2=123)`
  - Maintains type safety and validation during updates
  - Uses Redis JSON path operations for efficient field-only updates
  - All field updates in a single aupdate call are atomic

### ⚠️ Compatibility Notice

- **Pydantic Version Constraint**: This version supports Pydantic up to 2.12.0 due to internal logic changes in newer versions
- A future release will include support for multiple Pydantic versions
- All previous versions also have the same Pydantic 2.12.0 limitation

## [1.0.1] - 2025-11-04

### ✨ Added

- **Non-Serializable Type Support**: Added support for non-serializable types (like `type` and other pickleable objects)
- **Pickle Storage**: Non-serializable types are now stored in Redis as pickle data for proper serialization
- **Optional Field Support**: Added support for optional fields in Redis types

## [1.0.0] - 2025-11-02

### 🚀 Major Changes - Native BaseModel Integration

This release introduces **native BaseModel compatibility**, making Redis types work seamlessly with Pydantic models without requiring explicit initialization.

### ✨ Added

- **Native Redis Type Integration**: Redis types now work directly with BaseModel - no need to initialize with `""`, `0`, etc.
- **Direct Field Assignment**: Use simple assignment like `name: RedisStr = ""` instead of `name: RedisStr = ""`
- **Enhanced Nested Operations**: Support for saving inner fields directly with `model.lst[1].save()`
- **Simplified Type Declarations**: All Redis types (RedisStr, RedisInt, RedisList, RedisDict, RedisBytes) now support native Python value assignment

### 🔄 Changed

- **BREAKING**: Removed `set()` function - Redis types now update automatically when modified
- **Simplified API**: Redis type actions now automatically update the Redis store

### 🛠️ Technical Improvements

- Streamlined type validation and serialization
- Improved IDE support for Redis types with native Python syntax
- Better integration with Pydantic's validation system
- Reduced boilerplate code for Redis type usage
