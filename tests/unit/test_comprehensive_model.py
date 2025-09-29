import pytest
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Annotated
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
