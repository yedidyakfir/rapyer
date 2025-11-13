import pytest

import rapyer
from tests.models.collection_types import (
    ListModel,
    DictModel,
    ComprehensiveTestModel,
    BaseModelListModel,
    BaseModelDictModel,
)
from tests.models.common import UserProfile, Product, NestedConfig, UserWithKeyModel
from tests.models.complex_types import (
    OuterModel,
    TestRedisModel,
    OuterModelWithRedisNested,
)
from tests.models.inheritance_types import BaseUserModel, AdminUserModel, UserRole
from tests.models.pickle_types import ModelWithUnserializableFields
from tests.models.redis_types import DirectRedisStringModel, MixedDirectRedisTypesModel
from tests.models.simple_types import (
    StrModel,
    IntModel,
    BoolModel,
    BytesModel,
    DatetimeModel,
)


@pytest.mark.parametrize(
    ["model_instance"],
    [
        [StrModel(name="test_user", description="test description")],
        [IntModel(count=42, score=100)],
        [BoolModel(is_active=True, is_deleted=False)],
        [BytesModel(data=b"test_data", binary_content=b"binary_test")],
        [DatetimeModel()],
        [ListModel(items=["item1", "item2"], numbers=[1, 2, 3])],
        [DictModel(data={"key1": "value1"}, config={"setting1": 10})],
        [
            ComprehensiveTestModel(
                tags=["tag1", "tag2"],
                metadata={"key": "value"},
                name="comprehensive",
                counter=5,
            )
        ],
        [OuterModel(user_data={"user": 123}, items=[10, 20])],
        [
            TestRedisModel(
                user_data={"test": 456}, items=[30, 40], description="test_redis"
            )
        ],
        [DirectRedisStringModel(name="redis_string_test")],
        [
            MixedDirectRedisTypesModel(
                name="mixed_test",
                count=99,
                active=True,
                tags=["redis1", "redis2"],
                config={"config_key": 100},
            )
        ],
        # Complex nested models with BaseModel objects
        [
            BaseModelListModel(
                users=[
                    UserProfile(name="Alice", age=30, email="alice@test.com"),
                    UserProfile(name="Bob", age=25, email="bob@test.com"),
                ],
                products=[
                    Product(name="laptop", price=1000, in_stock=True),
                    Product(name="mouse", price=25, in_stock=False),
                ],
                configs=[
                    NestedConfig(
                        settings={"theme": "dark", "lang": "en"},
                        options=["feature1", "feature2"],
                    )
                ],
            )
        ],
        [
            BaseModelDictModel(
                metadata={
                    "admin": UserProfile(name="Admin", age=35, email="admin@test.com"),
                    "guest": UserProfile(name="Guest", age=22, email="guest@test.com"),
                }
            )
        ],
        # Deeply nested models
        [
            OuterModelWithRedisNested(
                outer_data=[1, 2, 3, 4, 5],
            )
        ],
        # Inheritance models
        [
            BaseUserModel(
                name="base_user",
                email="base@example.com",
                age=28,
                is_active=True,
                tags=["tag1", "tag2", "tag3"],
                metadata={"level": "basic", "department": "IT"},
                role=UserRole.USER,
                optional_field="optional_value",
                scores=[95, 87, 92],
            )
        ],
        [
            AdminUserModel(
                name="admin_user",
                email="admin@example.com",
                age=35,
                is_active=True,
                tags=["admin", "supervisor"],
                metadata={"level": "senior", "department": "Management"},
                role=UserRole.ADMIN,
                admin_level=5,
                permissions=["read", "write", "delete", "admin"],
                managed_users={"user1": "John Doe", "user2": "Jane Smith"},
                is_super_admin=True,
                admin_notes="Senior administrator with full privileges",
                backup_email="admin.backup@example.com",
                access_codes=[2001, 2002, 2003],
            )
        ],
        # Models with picklable/unserializable fields
        [ModelWithUnserializableFields(value=123, python_type=AdminUserModel)],
        # Models with custom key annotations
        [
            UserWithKeyModel(
                user_id="custom_user_key_123",
                name="Key User",
                email="keyuser@example.com",
                age=32,
            )
        ],
    ],
)
@pytest.mark.asyncio
async def test_rapyer_get_functionality_sanity(model_instance):
    # Arrange
    await model_instance.save()
    redis_key = model_instance.key

    # Act
    retrieved_model = await rapyer.get(redis_key)

    # Assert
    assert retrieved_model == model_instance
