import pytest
import pytest_asyncio

from tests.models.simple_types import IntModel, StrModel


@pytest_asyncio.fixture
async def create_indices(redis_client):
    # Create index for IntModel
    await IntModel.acreate_index()
    await StrModel.acreate_index()

    yield

    await IntModel.adelete_index()
    await StrModel.adelete_index()


@pytest.mark.asyncio
async def test_afind_with_single_expression_sanity(create_indices):
    # Arrange
    models = [
        IntModel(count=5, score=50),
        IntModel(count=10, score=100),
        IntModel(count=15, score=150),
        IntModel(count=20, score=200),
    ]
    await IntModel.ainsert(*models)

    # Act
    IntModel.init_class()
    found_models = await IntModel.afind(IntModel.count > 10)

    # Assert
    assert len(found_models) == 2
    for model in models:
        if model.count > 10:
            assert model in found_models


@pytest.mark.asyncio
async def test_afind_with_multiple_expressions_sanity(create_indices):
    # Arrange
    models = [
        IntModel(count=5, score=50),
        IntModel(count=10, score=100),
        IntModel(count=15, score=150),
        IntModel(count=20, score=200),
    ]

    for model in models:
        await model.asave()

    # Act
    IntModel.init_class()
    found_models = await IntModel.afind(IntModel.count >= 10, IntModel.score <= 150)

    # Assert
    assert len(found_models) == 2
    counts = [m.count for m in found_models]
    assert 10 in counts
    assert 15 in counts


@pytest.mark.asyncio
async def test_afind_with_combined_expressions_sanity(create_indices):
    # Arrange
    models = [
        IntModel(count=5, score=50),
        IntModel(count=10, score=100),
        IntModel(count=15, score=150),
        IntModel(count=20, score=200),
    ]

    for model in models:
        await model.asave()

    # Act
    IntModel.init_class()
    expression = (IntModel.count > 5) & (IntModel.score < 180)
    found_models = await IntModel.afind(expression)

    # Assert
    assert len(found_models) == 2
    counts = [m.count for m in found_models]
    assert 10 in counts
    assert 15 in counts


@pytest.mark.asyncio
async def test_afind_with_or_expression_sanity(create_indices):
    # Arrange
    models = [
        IntModel(count=5, score=50),
        IntModel(count=10, score=100),
        IntModel(count=15, score=150),
        IntModel(count=20, score=200),
    ]

    for model in models:
        await model.asave()

    # Act
    IntModel.init_class()
    expression = (IntModel.count <= 5) | (IntModel.count >= 20)
    found_models = await IntModel.afind(expression)

    # Assert
    assert len(found_models) == 2
    counts = [m.count for m in found_models]
    assert 5 in counts
    assert 20 in counts


@pytest.mark.asyncio
async def test_afind_without_expressions_returns_all_sanity():
    # Arrange
    models = [
        IntModel(count=5, score=50),
        IntModel(count=10, score=100),
        IntModel(count=15, score=150),
    ]

    for model in models:
        await model.asave()

    # Act
    found_models = await IntModel.afind()

    # Assert
    assert len(found_models) == 3
    counts = [m.count for m in found_models]
    assert 5 in counts
    assert 10 in counts
    assert 15 in counts


@pytest.mark.asyncio
async def test_afind_with_string_field_expression_sanity(create_indices):
    # Arrange
    models = [
        StrModel(name="Alice", description="Engineer"),
        StrModel(name="Bob", description="Manager"),
        StrModel(name="Charlie", description="Designer"),
        StrModel(name="David", description="Engineer"),
    ]

    for model in models:
        await model.asave()

    # Act
    StrModel.init_class()
    found_models = await StrModel.afind(StrModel.name == "Alice")

    # Assert
    assert len(found_models) == 1
    assert found_models[0].name == "Alice"


@pytest.mark.asyncio
async def test_afind_with_not_expression_sanity(create_indices):
    # Arrange
    models = [
        IntModel(count=5, score=50),
        IntModel(count=10, score=100),
        IntModel(count=15, score=150),
    ]

    for model in models:
        await model.asave()

    # Act
    IntModel.init_class()
    expression = ~(IntModel.count == 10)
    found_models = await IntModel.afind(expression)

    # Assert
    assert len(found_models) == 2
    counts = [m.count for m in found_models]
    assert 5 in counts
    assert 15 in counts
