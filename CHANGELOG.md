# Changelog

## [1.0.2] - 2025-11-05

### ✨ Added

- **Inheritance Model Support**: Added support for inheritance models - models that inherit from a Redis model still create a Redis model with full functionality

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
