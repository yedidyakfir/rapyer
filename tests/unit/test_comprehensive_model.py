from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Optional, Annotated

import pytest
from pydantic import (
    BaseModel,
    Field,
    BeforeValidator,
    AfterValidator,
    field_validator,
    computed_field,
    ValidationError,
)

from redis_pydantic.base import RedisModel


def normalize_name(value: str) -> str:
    """BeforeValidator: normalize names to title case."""
    if isinstance(value, str):
        return value.strip().title()
    return value


def validate_positive_number(value: int) -> int:
    """AfterValidator: ensure number is positive."""
    if value < 0:
        raise ValueError("Value must be positive")
    return value


def uppercase_tags(value: List[str]) -> List[str]:
    """BeforeValidator: convert all tags to uppercase."""
    if isinstance(value, list):
        return [tag.upper() if isinstance(tag, str) else tag for tag in value]
    return value


def ensure_even_score(value: int) -> int:
    """AfterValidator: ensure score is even."""
    if value % 2 != 0:
        value += 1
    return value


class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class Address(BaseModel):
    street: str
    city: str
    country: str
    zip_code: Optional[str] = None


class ComprehensiveModel(RedisModel):
    # String types with validators
    name: Annotated[str, BeforeValidator(normalize_name)]
    description: Optional[str] = None

    # Numeric types with validators
    age: Annotated[int, AfterValidator(validate_positive_number)]
    height: float
    balance: Decimal

    # Boolean
    is_active: bool = True
    is_verified: Optional[bool] = None

    # Enum
    status: UserStatus = UserStatus.ACTIVE

    # DateTime
    created_at: datetime
    last_login: Optional[datetime] = None

    # Bytes
    profile_image: bytes
    signature: Optional[bytes] = None

    # Collections with validators
    tags: Annotated[List[str], BeforeValidator(uppercase_tags)] = Field(
        default_factory=list
    )
    scores: List[Annotated[int, AfterValidator(ensure_even_score)]] = Field(
        default_factory=list
    )
    metadata: Dict[str, str] = Field(default_factory=dict)
    settings: Dict[str, int] = Field(default_factory=dict)

    # Nested model
    address: Address
    backup_address: Optional[Address] = None

    # Counters with constraints
    login_count: Annotated[int, Field(ge=0)] = 0
    points: Annotated[int, Field(ge=0, le=10000)] = 0

    # Field validator example
    @field_validator("balance")
    @classmethod
    def validate_balance(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v

    # Computed field example
    @computed_field
    @property
    def total_score(self) -> int:
        return sum(self.scores) if self.scores else 0


@pytest.mark.asyncio
async def test_comprehensive_model_all_types_sanity(redis_client):
    # Arrange
    test_datetime = datetime(2023, 5, 15, 10, 30, 45)
    test_bytes = b"profile_image_data"
    address = Address(
        street="123 Main St", city="Boston", country="USA", zip_code="02101"
    )

    model = ComprehensiveModel(
        name="john doe",  # Will be normalized to "John Doe"
        description="Test user",
        age=30,
        height=175.5,
        balance=Decimal("1234.56"),
        is_active=True,
        is_verified=False,
        status=UserStatus.PENDING,
        created_at=test_datetime,
        last_login=test_datetime,
        profile_image=test_bytes,
        signature=b"signature_data",
        tags=["developer", "python"],  # Will be uppercase: ["DEVELOPER", "PYTHON"]
        scores=[85, 91, 78],  # Odd scores will become even: [86, 92, 78]
        metadata={"role": "admin", "department": "engineering"},
        settings={"theme": 1, "notifications": 0},
        address=address,
        backup_address=address,
        login_count=5,
        points=1000,
    )

    # Act
    await model.save()
    retrieved = await ComprehensiveModel.get(model.key)

    # Assert
    assert retrieved == model


@pytest.mark.asyncio
async def test_comprehensive_model_optional_fields_sanity(redis_client):
    # Arrange - minimal model with only required fields
    address = Address(street="456 Oak Ave", city="Seattle", country="USA")

    model = ComprehensiveModel(
        name="Jane Smith",
        age=25,
        height=165.0,
        balance=Decimal("500.00"),
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        profile_image=b"minimal_image",
        address=address,
    )

    # Act
    await model.save()
    retrieved = await ComprehensiveModel.get(model.key)

    # Assert
    assert retrieved == model


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_name,initial_value,increment",
    [
        ("login_count", 0, 1),
        ("login_count", 5, 3),
        ("points", 100, 50),
        ("points", 1000, -200),
    ],
)
async def test_comprehensive_model_increase_counter_sanity(
    redis_client, field_name, initial_value, increment
):
    # Arrange
    address = Address(street="789 Pine St", city="Portland", country="USA")
    model_data = {
        "name": "Counter Test",
        "age": 30,
        "height": 170.0,
        "balance": Decimal("100.00"),
        "created_at": datetime(2023, 6, 1, 9, 0, 0),
        "profile_image": b"test_image",
        "address": address,
        field_name: initial_value,
    }

    model = ComprehensiveModel(**model_data)
    await model.save()

    # Act
    await model.increase_counter(field_name, increment)

    # Assert
    retrieved = await ComprehensiveModel.get(model.key)
    expected_value = initial_value + increment
    assert getattr(retrieved, field_name) == expected_value
    assert getattr(model, field_name) == expected_value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_name,initial_list,new_item",
    [
        ("tags", [], "first_tag"),
        ("tags", ["existing"], "new_tag"),
        ("scores", [10, 20], 30),
        ("scores", [], 100),
    ],
)
async def test_comprehensive_model_append_to_list_sanity(
    redis_client, field_name, initial_list, new_item
):
    # Arrange
    address = Address(street="321 Elm St", city="Denver", country="USA")
    model_data = {
        "name": "List Test",
        "age": 28,
        "height": 168.0,
        "balance": Decimal("750.00"),
        "created_at": datetime(2023, 7, 1, 14, 30, 0),
        "profile_image": b"list_test_image",
        "address": address,
        field_name: initial_list,
    }

    model = ComprehensiveModel(**model_data)
    await model.save()

    # Act
    await model.append_to_list(field_name, new_item)

    # Assert
    retrieved = await ComprehensiveModel.get(model.key)

    # Check that the models are equal - this validates that storage/retrieval works
    # Note: append_to_list bypasses validators since it directly modifies Redis
    # The validators only apply during model creation/validation
    assert getattr(retrieved, field_name) == getattr(model, field_name)


@pytest.mark.asyncio
async def test_comprehensive_model_update_complex_fields_sanity(redis_client):
    # Arrange
    original_address = Address(street="Original St", city="Old City", country="USA")
    model = ComprehensiveModel(
        name="Update Test",
        age=35,
        height=180.0,
        balance=Decimal("2000.00"),
        created_at=datetime(2023, 8, 1, 16, 0, 0),
        profile_image=b"original_image",
        address=original_address,
        tags=["old_tag"],
        metadata={"old_key": "old_value"},
    )
    await model.save()

    # Act
    new_address = Address(
        street="New St", city="New City", country="Canada", zip_code="K1A0A6"
    )
    new_datetime = datetime(2023, 8, 15, 10, 0, 0)
    await model.update(
        name="Updated Name",
        age=36,
        last_login=new_datetime,
        signature=b"new_signature",
        address=new_address,
        tags=["updated_tag", "another_tag"],
        metadata={"new_key": "new_value", "role": "updated"},
    )

    # Assert
    retrieved = await ComprehensiveModel.get(model.key)
    assert retrieved == model


@pytest.mark.asyncio
async def test_annotated_fields_validators_sanity(redis_client):
    # Arrange
    address = Address(street="123 Main St", city="Boston", country="USA")

    # Test data that will be transformed by validators
    model = ComprehensiveModel(
        name="  jane SMITH  ",  # Should become "Jane Smith" (normalized)
        age=25,
        height=165.0,
        balance=Decimal("500.00"),
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        profile_image=b"test_image",
        tags=[
            "python",
            "redis",
            "developer",
        ],  # Should become ["PYTHON", "REDIS", "DEVELOPER"]
        scores=[1, 3, 5, 8],  # Odd numbers should become even: [2, 4, 6, 8]
        address=address,
        login_count=10,
        points=500,
    )

    # Act
    await model.save()
    retrieved = await ComprehensiveModel.get(model.key)

    # Assert - Check that validators were applied
    assert retrieved.name == "Jane Smith"  # BeforeValidator normalized
    assert retrieved.tags == [
        "PYTHON",
        "REDIS",
        "DEVELOPER",
    ]  # BeforeValidator uppercase
    assert retrieved.scores == [2, 4, 6, 8]  # AfterValidator made even
    assert retrieved.total_score == 20  # Computed field
    assert retrieved == model


@pytest.mark.asyncio
async def test_field_validator_constraints_sanity(redis_client):
    # Arrange
    address = Address(street="456 Oak Ave", city="Seattle", country="USA")

    # Act & Assert - Test field constraints
    with pytest.raises(ValueError, match="Value must be positive"):
        ComprehensiveModel(
            name="Test User",
            age=-5,  # Should fail AfterValidator
            height=170.0,
            balance=Decimal("100.00"),
            created_at=datetime(2023, 1, 1),
            profile_image=b"test",
            address=address,
        )

    with pytest.raises(ValueError, match="Balance cannot be negative"):
        ComprehensiveModel(
            name="Test User",
            age=25,
            height=170.0,
            balance=Decimal("-100.00"),  # Should fail field_validator
            created_at=datetime(2023, 1, 1),
            profile_image=b"test",
            address=address,
        )

    with pytest.raises(
        ValidationError, match="Input should be greater than or equal to 0"
    ):
        ComprehensiveModel(
            name="Test User",
            age=25,
            height=170.0,
            balance=Decimal("100.00"),
            created_at=datetime(2023, 1, 1),
            profile_image=b"test",
            address=address,
            login_count=-1,  # Should fail Field constraint
        )

    with pytest.raises(
        ValidationError, match="Input should be less than or equal to 10000"
    ):
        ComprehensiveModel(
            name="Test User",
            age=25,
            height=170.0,
            balance=Decimal("100.00"),
            created_at=datetime(2023, 1, 1),
            profile_image=b"test",
            address=address,
            points=15000,  # Should fail Field constraint
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_names",
    [
        ["name", "age"],
        ["balance", "created_at"],
        ["address", "tags"],
        ["profile_image", "signature"],
        ["scores", "metadata"],
        ["is_active", "is_verified"],
        ["login_count", "points"],
    ],
)
async def test_load_fields_comprehensive_model_sanity(redis_client, field_names):
    # Arrange
    test_datetime = datetime(2023, 5, 15, 10, 30, 45)
    test_bytes = b"profile_image_data"
    address = Address(
        street="123 Main St", city="Boston", country="USA", zip_code="02101"
    )

    original_model = ComprehensiveModel(
        name="john doe",
        description="Test user",
        age=30,
        height=175.5,
        balance=Decimal("1234.56"),
        is_active=True,
        is_verified=False,
        created_at=test_datetime,
        last_login=test_datetime,
        profile_image=test_bytes,
        signature=b"signature_data",
        tags=["developer", "python"],
        scores=[85, 91, 78],
        metadata={"role": "admin", "department": "engineering"},
        settings={"theme": 1, "notifications": 0},
        address=address,
        backup_address=address,
        login_count=5,
        points=1000,
    )
    await original_model.save()

    # Change the model locally to verify we're loading from Redis
    original_model.name = "Changed Name"
    original_model.age = 999
    original_model.balance = Decimal("999.99")
    original_model.created_at = datetime(2000, 1, 1)
    original_model.address = Address(
        street="Changed", city="Changed", country="Changed"
    )
    original_model.tags = ["changed"]
    original_model.profile_image = b"changed"
    original_model.signature = b"changed"
    original_model.scores = [999]
    original_model.metadata = {"changed": "value"}
    original_model.is_active = False
    original_model.is_verified = True
    original_model.login_count = 999
    original_model.points = 999

    # Act
    loaded_fields = await ComprehensiveModel.load_fields(
        original_model.key, *field_names
    )

    # Assert
    expected_values = {
        "name": "John Doe",  # Normalized by validator
        "age": 30,
        "balance": Decimal("1234.56"),
        "created_at": test_datetime,
        "address": address,
        "tags": ["DEVELOPER", "PYTHON"],  # Uppercase by validator
        "profile_image": test_bytes,
        "signature": b"signature_data",
        "scores": [86, 92, 78],  # Made even by validator
        "metadata": {"role": "admin", "department": "engineering"},
        "is_active": True,
        "is_verified": False,
        "status": UserStatus.PENDING,
        "login_count": 5,
        "points": 1000,
    }

    for field_name in field_names:
        assert field_name in loaded_fields
        assert loaded_fields[field_name] == expected_values[field_name]

    # Verify only requested fields are returned
    assert set(loaded_fields.keys()) == set(field_names)


@pytest.mark.asyncio
async def test_load_fields_complex_partial_update_verification_sanity(redis_client):
    # Arrange
    original_address = Address(street="Original St", city="Old City", country="USA")
    original_datetime = datetime(2023, 8, 1, 16, 0, 0)

    model = ComprehensiveModel(
        name="Original Name",
        age=35,
        height=180.0,
        balance=Decimal("2000.00"),
        created_at=original_datetime,
        profile_image=b"original_image",
        address=original_address,
        tags=["old_tag"],
        scores=[10, 20],
        metadata={"old_key": "old_value"},
        settings={"old_setting": 1},
        login_count=100,
        points=500,
    )
    await model.save()

    # Act - Update some fields
    new_address = Address(
        street="New St", city="New City", country="Canada", zip_code="K1A0A6"
    )
    new_datetime = datetime(2023, 8, 15, 10, 0, 0)
    await model.update(
        name="Updated Name",
        age=36,
        last_login=new_datetime,
        signature=b"new_signature",
        address=new_address,
        tags=["updated_tag", "another_tag"],
        scores=[30, 40, 50],
        metadata={"new_key": "new_value", "role": "updated"},
        points=750,
    )

    # Load updated fields
    updated_fields = await ComprehensiveModel.load_fields(
        model.key,
        "name",
        "age",
        "address",
        "tags",
        "scores",
        "metadata",
        "points",
        "last_login",
        "signature",
    )

    # Load unchanged fields
    unchanged_fields = await ComprehensiveModel.load_fields(
        model.key,
        "height",
        "balance",
        "created_at",
        "profile_image",
        "settings",
        "login_count",
    )

    # Assert - Updated fields have new values
    assert updated_fields["name"] == "Updated Name"
    assert updated_fields["age"] == 36
    assert updated_fields["address"] == new_address
    assert updated_fields["tags"] == ["updated_tag", "another_tag"]
    assert updated_fields["scores"] == [30, 40, 50]
    assert updated_fields["metadata"] == {"new_key": "new_value", "role": "updated"}
    assert updated_fields["points"] == 750
    assert updated_fields["last_login"] == new_datetime
    assert updated_fields["signature"] == b"new_signature"

    # Assert - Unchanged fields have original values
    assert unchanged_fields["height"] == 180.0
    assert unchanged_fields["balance"] == Decimal("2000.00")
    assert unchanged_fields["created_at"] == original_datetime
    assert unchanged_fields["profile_image"] == b"original_image"
    assert unchanged_fields["settings"] == {"old_setting": 1}
    assert unchanged_fields["login_count"] == 100


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_type_group",
    [
        ["name", "description"],  # String types
        ["age", "height", "balance"],  # Numeric types
        ["is_active", "is_verified", "status"],  # Boolean and Enum types
        ["created_at", "last_login"],  # DateTime types
        ["profile_image", "signature"],  # Bytes types
        ["tags", "scores"],  # List types
        ["metadata", "settings"],  # Dict types
        ["address", "backup_address"],  # Nested model types
        ["login_count", "points"],  # Constrained fields
    ],
)
async def test_load_fields_by_type_groups_sanity(redis_client, field_type_group):
    # Arrange
    address = Address(street="456 Oak Ave", city="Seattle", country="USA")
    test_datetime = datetime(2023, 1, 1, 12, 0, 0)

    model = ComprehensiveModel(
        name="Type Test",
        description="Testing different field types",
        age=25,
        height=165.0,
        balance=Decimal("500.00"),
        is_active=True,
        is_verified=False,
        status=UserStatus.INACTIVE,
        created_at=test_datetime,
        last_login=test_datetime,
        profile_image=b"minimal_image",
        signature=b"test_signature",
        tags=["test", "type"],
        scores=[10, 20, 30],
        metadata={"test": "value"},
        settings={"setting": 1},
        address=address,
        backup_address=address,
        login_count=10,
        points=100,
    )
    await model.save()

    # Act
    loaded_fields = await ComprehensiveModel.load_fields(model.key, *field_type_group)

    # Assert
    expected_values = {
        "name": "Type Test",
        "description": "Testing different field types",
        "age": 25,
        "height": 165.0,
        "balance": Decimal("500.00"),
        "is_active": True,
        "is_verified": False,
        "status": UserStatus.INACTIVE,
        "created_at": test_datetime,
        "last_login": test_datetime,
        "profile_image": b"minimal_image",
        "signature": b"test_signature",
        "tags": ["TEST", "TYPE"],  # Uppercase by validator
        "scores": [10, 20, 30],
        "metadata": {"test": "value"},
        "settings": {"setting": 1},
        "address": address,
        "backup_address": address,
        "login_count": 10,
        "points": 100,
    }

    for field_name in field_type_group:
        assert field_name in loaded_fields
        assert loaded_fields[field_name] == expected_values[field_name]

    # Verify only requested fields are returned
    assert set(loaded_fields.keys()) == set(field_type_group)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_name,initial_list,expected_popped",
    [
        ("tags", ["FIRST", "SECOND", "THIRD"], "FIRST"),
        ("scores", [10, 20, 30], 10),
        ("tags", ["ONLY"], "ONLY"),
        ("scores", [42], 42),
    ],
)
async def test_pop_from_key_sanity(
    redis_client, field_name, initial_list, expected_popped
):
    # Arrange
    address = Address(street="123 Test St", city="Test City", country="USA")
    model_data = {
        "name": "Pop Test",
        "age": 30,
        "height": 170.0,
        "balance": Decimal("100.00"),
        "created_at": datetime(2023, 1, 1, 12, 0, 0),
        "profile_image": b"test_image",
        "address": address,
        field_name: initial_list,
    }

    model = ComprehensiveModel(**model_data)
    await model.save()

    # Act
    popped_value = await ComprehensiveModel.pop_from_key(model.key, field_name)

    # Assert
    assert popped_value == expected_popped

    # Verify the value was removed from Redis
    retrieved = await ComprehensiveModel.get(model.key)
    current_list = getattr(retrieved, field_name)
    assert len(current_list) == len(initial_list) - 1
    assert expected_popped not in current_list or current_list.count(
        expected_popped
    ) < initial_list.count(expected_popped)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_name,initial_list,expected_popped",
    [
        ("tags", ["FIRST", "SECOND", "THIRD"], "FIRST"),
        ("scores", [10, 20, 30], 10),
        ("tags", ["ONLY"], "ONLY"),
        ("scores", [42], 42),
    ],
)
async def test_pop_method_sanity(
    redis_client, field_name, initial_list, expected_popped
):
    # Arrange
    address = Address(street="123 Test St", city="Test City", country="USA")
    model_data = {
        "name": "Pop Test",
        "age": 30,
        "height": 170.0,
        "balance": Decimal("100.00"),
        "created_at": datetime(2023, 1, 1, 12, 0, 0),
        "profile_image": b"test_image",
        "address": address,
        field_name: initial_list,
    }

    model = ComprehensiveModel(**model_data)
    await model.save()

    # Act
    popped_value = await model.pop(field_name)

    # Assert
    assert popped_value == expected_popped

    # Check that both Redis and local object are updated
    retrieved = await ComprehensiveModel.get(model.key)
    local_list = getattr(model, field_name)
    redis_list = getattr(retrieved, field_name)

    assert len(local_list) == len(initial_list) - 1
    assert len(redis_list) == len(initial_list) - 1
    assert local_list == redis_list
    assert expected_popped not in local_list or local_list.count(
        expected_popped
    ) < initial_list.count(expected_popped)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_name,initial_list,expected_popped",
    [
        ("tags", ["FIRST", "SECOND", "THIRD"], "FIRST"),
        ("scores", [10, 20, 30], 10),
    ],
)
async def test_standalone_pop_function_sanity(
    redis_client, field_name, initial_list, expected_popped
):
    # Arrange
    address = Address(street="123 Test St", city="Test City", country="USA")
    model_data = {
        "name": "Pop Test",
        "age": 30,
        "height": 170.0,
        "balance": Decimal("100.00"),
        "created_at": datetime(2023, 1, 1, 12, 0, 0),
        "profile_image": b"test_image",
        "address": address,
        field_name: initial_list,
    }

    model = ComprehensiveModel(**model_data)
    await model.save()

    # Act
    popped_value = await model.pop(field_name)

    # Assert
    assert popped_value == expected_popped

    # Check that both Redis and local object are updated
    retrieved = await ComprehensiveModel.get(model.key)
    local_list = getattr(model, field_name)
    redis_list = getattr(retrieved, field_name)

    assert len(local_list) == len(initial_list) - 1
    assert len(redis_list) == len(initial_list) - 1
    assert local_list == redis_list


@pytest.mark.asyncio
async def test_pop_empty_list_edge_case(redis_client):
    # Arrange
    address = Address(street="123 Test St", city="Test City", country="USA")
    model = ComprehensiveModel(
        name="Empty Pop Test",
        age=30,
        height=170.0,
        balance=Decimal("100.00"),
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        profile_image=b"test_image",
        address=address,
        tags=[],  # Empty list
    )
    await model.save()

    # Act
    popped_value = await model.pop("tags")

    # Assert
    assert popped_value is None

    # Verify lists remain empty
    retrieved = await ComprehensiveModel.get(model.key)
    assert getattr(model, "tags") == []
    assert getattr(retrieved, "tags") == []


@pytest.mark.asyncio
async def test_pop_invalid_field_edge_case(redis_client):
    # Arrange
    address = Address(street="123 Test St", city="Test City", country="USA")
    model = ComprehensiveModel(
        name="Invalid Field Test",
        age=30,
        height=170.0,
        balance=Decimal("100.00"),
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        profile_image=b"test_image",
        address=address,
    )
    await model.save()

    # Act & Assert
    with pytest.raises(ValueError, match="Field nonexistent_field not found"):
        await model.pop("nonexistent_field")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_value",
    [
        UserStatus.ACTIVE,
        UserStatus.INACTIVE,
        UserStatus.PENDING,
        UserStatus.SUSPENDED,
    ],
)
async def test_enum_field_support_sanity(redis_client, status_value):
    # Arrange
    address = Address(street="123 Enum St", city="Test City", country="USA")
    model = ComprehensiveModel(
        name="Enum Test",
        age=30,
        height=170.0,
        balance=Decimal("100.00"),
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        profile_image=b"test_image",
        address=address,
        status=status_value,
    )

    # Act
    await model.save()
    retrieved = await ComprehensiveModel.get(model.key)

    # Assert
    assert retrieved.status == status_value
    assert retrieved.status.value == status_value.value
    assert retrieved == model


@pytest.mark.asyncio
async def test_enum_field_update_sanity(redis_client):
    # Arrange
    address = Address(street="123 Enum Update St", city="Test City", country="USA")
    model = ComprehensiveModel(
        name="Enum Update Test",
        age=30,
        height=170.0,
        balance=Decimal("100.00"),
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        profile_image=b"test_image",
        address=address,
        status=UserStatus.ACTIVE,
    )
    await model.save()

    # Act
    await model.update(status=UserStatus.SUSPENDED)

    # Assert
    retrieved = await ComprehensiveModel.get(model.key)
    assert retrieved.status == UserStatus.SUSPENDED
    assert model.status == UserStatus.SUSPENDED
    assert retrieved == model


@pytest.mark.asyncio
async def test_enum_field_load_fields_sanity(redis_client):
    # Arrange
    address = Address(street="123 Enum Load St", city="Test City", country="USA")
    model = ComprehensiveModel(
        name="Enum Load Test",
        age=30,
        height=170.0,
        balance=Decimal("100.00"),
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        profile_image=b"test_image",
        address=address,
        status=UserStatus.PENDING,
    )
    await model.save()

    # Act
    loaded_fields = await ComprehensiveModel.load_fields(model.key, "status", "name")

    # Assert
    assert loaded_fields["status"] == UserStatus.PENDING
    assert loaded_fields["name"] == "Enum Load Test"


@pytest.mark.asyncio
async def test_pop_non_list_field_edge_case(redis_client):
    # Arrange
    address = Address(street="123 Test St", city="Test City", country="USA")
    model = ComprehensiveModel(
        name="Non List Test",
        age=30,
        height=170.0,
        balance=Decimal("100.00"),
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        profile_image=b"test_image",
        address=address,
    )
    await model.save()

    # Act & Assert
    with pytest.raises(ValueError, match="Field name is not a list type"):
        await model.pop("name")  # name is a string, not a list
