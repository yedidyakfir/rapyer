import pytest
import pytest_asyncio

from tests.models.index_types import IndexTestModel, BaseIndexModel


@pytest_asyncio.fixture
async def create_indices(redis_client):
    # Create index for IntModel
    await IndexTestModel.acreate_index()
    await BaseIndexModel.acreate_index()

    yield

    await IndexTestModel.adelete_index()
    await BaseIndexModel.adelete_index()


@pytest.mark.asyncio
async def test_afind_with_single_expression_sanity(create_indices):
    # Arrange
    models = [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
        IndexTestModel(name="David", age=40, description="Director"),
    ]
    await IndexTestModel.ainsert(*models)

    # Act
    IndexTestModel.init_class()
    found_models = await IndexTestModel.afind(IndexTestModel.age > 30)

    # Assert
    assert len(found_models) == 2
    for model in models:
        if model.age > 30:
            assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_multiple_expressions_sanity(create_indices):
    # Arrange
    models = [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
        IndexTestModel(name="David", age=40, description="Director"),
    ]
    await IndexTestModel.ainsert(*models)

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
async def test_afind_with_combined_expressions_sanity(create_indices):
    # Arrange
    models = [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
        IndexTestModel(name="David", age=40, description="Director"),
    ]
    await IndexTestModel.ainsert(*models)

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
async def test_afind_with_or_expression_sanity(create_indices):
    # Arrange
    models = [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
        IndexTestModel(name="David", age=40, description="Director"),
    ]
    await IndexTestModel.ainsert(*models)

    # Act
    IndexTestModel.init_class()
    expression = (IndexTestModel.age <= 25) | (IndexTestModel.age >= 40)
    found_models = await IndexTestModel.afind(expression)

    # Assert
    assert len(found_models) == 2
    for model in models:
        if model.age <= 25 or model.age >= 40:
            assert model in found_models


@pytest.mark.asyncio
async def test_afind_without_expressions_returns_all_sanity():
    # Arrange
    models = [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
    ]
    await IndexTestModel.ainsert(*models)

    # Act
    found_models = await IndexTestModel.afind()

    # Assert
    assert len(found_models) == 3
    for model in models:
        assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_string_field_expression_sanity(create_indices):
    # Arrange
    models = [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
        IndexTestModel(name="David", age=40, description="Engineer"),
    ]
    await IndexTestModel.ainsert(*models)

    # Act
    IndexTestModel.init_class()
    found_models = await IndexTestModel.afind(IndexTestModel.name == "Alice")

    # Assert
    assert len(found_models) == 1
    for model in models:
        if model.name == "Alice":
            assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_not_expression_sanity(create_indices):
    # Arrange
    models = [
        IndexTestModel(name="Alice", age=25, description="Engineer"),
        IndexTestModel(name="Bob", age=30, description="Manager"),
        IndexTestModel(name="Charlie", age=35, description="Designer"),
    ]
    await IndexTestModel.ainsert(*models)

    # Act
    IndexTestModel.init_class()
    expression = ~(IndexTestModel.age == 30)
    found_models = await IndexTestModel.afind(expression)

    # Assert
    assert len(found_models) == 2
    for model in models:
        if model.age != 30:
            assert model in found_models
