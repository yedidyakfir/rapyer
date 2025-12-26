import pytest
import pytest_asyncio
from datetime import datetime, timedelta

from tests.models.index_types import (
    IndexTestModel, 
    BaseIndexModel,
    UserIndexModel,
    ProductIndexModel
)


@pytest_asyncio.fixture
async def create_indices(redis_client):
    # Create index for IntModel
    await IndexTestModel.acreate_index()
    await BaseIndexModel.acreate_index()

    yield

    await IndexTestModel.adelete_index()
    await BaseIndexModel.adelete_index()


@pytest.fixture
def test_models():
    return [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
        IndexTestModel(name="David", age=40, description="Director"),
    ]


@pytest_asyncio.fixture
async def inserted_test_models(test_models):
    await IndexTestModel.ainsert(*test_models)
    return test_models


@pytest.mark.asyncio
async def test_afind_with_single_expression_sanity(create_indices, inserted_test_models):
    # Arrange
    models = inserted_test_models

    # Act
    IndexTestModel.init_class()
    found_models = await IndexTestModel.afind(IndexTestModel.age > 30)

    # Assert
    assert len(found_models) == 2
    for model in models:
        if model.age > 30:
            assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_multiple_expressions_sanity(create_indices, inserted_test_models):
    # Arrange
    models = inserted_test_models

    # Act
    IndexTestModel.init_class()
    found_models = await IndexTestModel.afind(
        IndexTestModel.age >= 30, IndexTestModel.name == "Charlie"
    )

    # Assert
    assert len(found_models) == 1
    for model in models:
        if model.age >= 30 and model.name == "Charlie":
            assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_combined_expressions_sanity(create_indices, inserted_test_models):
    # Arrange
    models = inserted_test_models

    # Act
    IndexTestModel.init_class()
    expression = (IndexTestModel.age > 25) & (IndexTestModel.age < 40)
    found_models = await IndexTestModel.afind(expression)

    # Assert
    assert len(found_models) == 2
    for model in models:
        if model.age > 25 and model.age < 40:
            assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_or_expression_sanity(create_indices, inserted_test_models):
    # Arrange
    models = inserted_test_models

    # Act
    IndexTestModel.init_class()
    expression = (IndexTestModel.age <= 25) | (IndexTestModel.age >= 40)
    found_models = await IndexTestModel.afind(expression)

    # Assert
    assert len(found_models) == 2
    for model in models:
        if model.age <= 25 or model.age >= 40:
            assert model in found_models


@pytest.fixture
def three_test_models():
    return [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
    ]


@pytest_asyncio.fixture
async def inserted_three_test_models(three_test_models):
    await IndexTestModel.ainsert(*three_test_models)
    return three_test_models


@pytest.mark.asyncio
async def test_afind_without_expressions_returns_all_sanity(inserted_three_test_models):
    # Arrange
    models = inserted_three_test_models

    # Act
    found_models = await IndexTestModel.afind()

    # Assert
    assert len(found_models) == 3
    for model in models:
        assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_string_field_expression_sanity(create_indices, inserted_test_models):
    # Arrange
    models = inserted_test_models

    # Act
    IndexTestModel.init_class()
    found_models = await IndexTestModel.afind(IndexTestModel.name == "Alice")

    # Assert
    assert len(found_models) == 1
    for model in models:
        if model.name == "Alice":
            assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_not_expression_sanity(create_indices, inserted_three_test_models):
    # Arrange
    models = inserted_three_test_models

    # Act
    IndexTestModel.init_class()
    expression = ~(IndexTestModel.age == 30)
    found_models = await IndexTestModel.afind(expression)

    # Assert
    assert len(found_models) == 2
    for model in models:
        if model.age != 30:
            assert model in found_models


# NOTE: Testing float type filtering (ProductIndexModel.price is float)
@pytest.mark.asyncio
async def test_afind_with_float_filtering_sanity(redis_client):
    # Arrange
    await ProductIndexModel.acreate_index()
    
    base_date = datetime(2024, 1, 1)
    product1 = ProductIndexModel(id="prod1", created_at=base_date, name="Laptop", price=1500.99)
    product2 = ProductIndexModel(id="prod2", created_at=base_date, name="Phone", price=899.50)
    product3 = ProductIndexModel(id="prod3", created_at=base_date, name="Tablet", price=599.99)
    product4 = ProductIndexModel(id="prod4", created_at=base_date, name="Watch", price=299.00)
    
    await ProductIndexModel.ainsert(product1, product2, product3, product4)
    
    # Act
    ProductIndexModel.init_class()
    found_models = await ProductIndexModel.afind(
        (ProductIndexModel.price >= 300.0) & (ProductIndexModel.price < 1000.0)
    )
    
    # Assert
    assert len(found_models) == 2
    assert product2 in found_models
    assert product3 in found_models
    assert product1 not in found_models
    assert product4 not in found_models
    
    # Cleanup
    await ProductIndexModel.adelete_index()


# NOTE: Testing datetime filtering
@pytest.mark.asyncio
async def test_afind_with_datetime_filtering_sanity(redis_client):
    # Arrange
    await BaseIndexModel.acreate_index()
    
    base_date = datetime(2024, 1, 1, 12, 0, 0)
    model1 = BaseIndexModel(id="model1", created_at=base_date - timedelta(days=10))
    model2 = BaseIndexModel(id="model2", created_at=base_date)
    model3 = BaseIndexModel(id="model3", created_at=base_date + timedelta(days=15))
    model4 = BaseIndexModel(id="model4", created_at=base_date + timedelta(days=30, hours=5))
    
    await BaseIndexModel.ainsert(model1, model2, model3, model4)
    
    # Act
    BaseIndexModel.init_class()
    # Filter by datetime range
    found_models = await BaseIndexModel.afind(
        (BaseIndexModel.created_at >= base_date) & 
        (BaseIndexModel.created_at < base_date + timedelta(days=20))
    )
    
    # Assert
    assert len(found_models) == 2
    assert model2 in found_models
    assert model3 in found_models
    assert model1 not in found_models
    assert model4 not in found_models
    
    # Cleanup
    await BaseIndexModel.adelete_index()


# NOTE: Testing filtering on inherited indexed fields
@pytest.mark.asyncio 
async def test_afind_with_inheritance_filtering_sanity(redis_client):
    # Arrange
    await UserIndexModel.acreate_index()
    await ProductIndexModel.acreate_index()
    
    base_date = datetime(2024, 1, 1)
    
    # Create UserIndexModel instances (inherits id and created_at from BaseIndexModel)
    user1 = UserIndexModel(id="user1", created_at=base_date, username="alice", email="alice@test.com")
    user2 = UserIndexModel(id="user2", created_at=base_date + timedelta(days=30), username="bob", email="bob@test.com")
    user3 = UserIndexModel(id="user3", created_at=base_date + timedelta(days=60), username="charlie", email="charlie@test.com")
    
    # Create ProductIndexModel instances
    product1 = ProductIndexModel(id="prod1", created_at=base_date, name="Laptop", price=1500.0)
    product2 = ProductIndexModel(id="prod2", created_at=base_date + timedelta(days=15), name="Phone", price=800.0)
    product3 = ProductIndexModel(id="prod3", created_at=base_date + timedelta(days=45), name="Tablet", price=600.0)
    
    await UserIndexModel.ainsert(user1, user2, user3)
    await ProductIndexModel.ainsert(product1, product2, product3)
    
    # Act - Filter users by inherited created_at field
    UserIndexModel.init_class()
    users_found = await UserIndexModel.afind(UserIndexModel.created_at > base_date + timedelta(days=20))
    
    # Act - Filter products by inherited field and own field
    ProductIndexModel.init_class()
    products_found = await ProductIndexModel.afind(
        (ProductIndexModel.created_at <= base_date + timedelta(days=30)) & (ProductIndexModel.price < 1000)
    )
    
    # Assert
    assert len(users_found) == 2
    assert user2 in users_found
    assert user3 in users_found
    
    assert len(products_found) == 2
    assert product2 in products_found
    assert product3 in products_found
    
    # Cleanup
    await UserIndexModel.adelete_index()
    await ProductIndexModel.adelete_index()
