# Rapyer Roadmap

This document outlines the planned features and improvements for Rapyer, the Redis Atomic Pydantic Engine Reactor.

## Phase 1: Complete Pipeline Redis Synchronization

### 🎯 Current Priority: Pipeline Actions for All Types

**Problem**: Currently, only list and dict operations (like `.update()` and `.append()`) automatically sync with Redis when used in pipeline mode. Other Redis types like integers and strings require manual synchronization.

**Goal**: Extend pipeline synchronization to all Redis types for complete atomic operations support.

#### Tasks:
- [ ] **RedisInt Pipeline Support**
  - Implement pipeline sync for `+=`, `-=`, `*=`, `/=` operators
  - Add pipeline support for `increase()` method
  - Ensure atomic increment/decrement operations in pipeline mode

- [ ] **RedisStr Pipeline Support**
  - Implement pipeline sync for `+=` (string concatenation)
  - Add pipeline support for string modification operations
  - Ensure atomic string updates in pipeline mode

- [ ] **RedisBytes Pipeline Support**
  - Implement pipeline sync for byte operations
  - Add atomic byte manipulation in pipeline mode

- [ ] **RedisDateTime Pipeline Support**
  - Implement pipeline sync for datetime modifications
  - Ensure atomic datetime updates

- [ ] **Testing & Validation**
  - Add comprehensive tests for all new pipeline operations
  - Verify atomic behavior under concurrent access
  - Performance benchmarking for pipeline operations

**Expected Benefits**:
- Complete atomic operation coverage for all Redis types
- Consistent developer experience across all data types
- Enhanced race condition prevention
- Better pipeline performance for mixed-type operations

## Phase 2: Enhanced Type System

### Advanced Type Support
- [ ] **Set Operations**: Implement RedisSet with atomic add/remove operations
- [ ] **Ordered Sets**: Redis sorted set integration with ranking operations
- [ ] **Geospatial Types**: Location-based data with radius queries
- [ ] **Stream Types**: Redis stream integration for event sourcing

### Type Optimization
- [ ] **Memory Optimization**: Reduce memory footprint for large collections
- [ ] **Serialization Performance**: Optimize JSON serialization for complex types
- [ ] **Custom Type Support**: Framework for user-defined Redis types

## Phase 3: Advanced Features

### Enhanced Concurrency
- [ ] **Distributed Locks**: Cross-process locking mechanisms
- [ ] **Transaction Rollback**: Automatic rollback on pipeline failures
- [ ] **Optimistic Locking**: Version-based conflict detection

### Developer Experience
- [ ] **CLI Tools**: Command-line utilities for Redis model inspection
- [ ] **Debug Mode**: Enhanced debugging for Redis operations
- [ ] **Migration Tools**: Schema migration support for model changes

### Performance & Monitoring
- [ ] **Metrics Collection**: Built-in performance monitoring
- [ ] **Connection Pooling**: Advanced Redis connection management
- [ ] **Async Batch Operations**: Efficient bulk operations

## Phase 4: Ecosystem Integration

### Framework Integration
- [ ] **FastAPI Plugin**: Seamless FastAPI integration
- [ ] **Django Integration**: Django ORM-style interface
- [ ] **SQLAlchemy Compatibility**: Migration path from SQL databases

### Deployment & Operations
- [ ] **Docker Support**: Official Docker images and examples
- [ ] **Kubernetes Operators**: Cloud-native deployment tools
- [ ] **Health Checks**: Built-in health monitoring endpoints

## Contributing

We welcome contributions to any of these roadmap items! Please see our contributing guidelines and feel free to:

- Pick up any unassigned task
- Propose new features or improvements
- Submit bug reports or performance issues
- Improve documentation and examples

## Timeline

- **Phase 1**: Q1 2025 - Complete pipeline synchronization
- **Phase 2**: Q2 2025 - Enhanced type system
- **Phase 3**: Q3-Q4 2025 - Advanced features
- **Phase 4**: 2026 - Ecosystem integration

*This roadmap is subject to change based on community feedback and project priorities.*