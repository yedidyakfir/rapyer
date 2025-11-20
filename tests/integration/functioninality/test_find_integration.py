import pytest

from tests.models.simple_types import StrModel, IntModel, BoolModel


@pytest.mark.asyncio
async def test_find_isolation_between_different_model_classes_sanity():
    # Arrange
    str_models = [StrModel(name=f"str_{i}", description=f"desc_{i}") for i in range(3)]
    int_models = [IntModel(count=i * 10, score=i * 100) for i in range(2)]
    bool_models = [
        BoolModel(is_active=bool(i % 2), is_deleted=not bool(i % 2)) for i in range(4)
    ]
    another_str_model = StrModel(name="another_str", description="another_desc")

    # Act - Save all models
    for model in str_models:
        await model.save()
    for model in int_models:
        await model.save()
    for model in bool_models:
        await model.save()

    # Find models for each class
    found_str_models = await StrModel.afind()
    found_int_models = await IntModel.afind()
    found_bool_models = await BoolModel.afind()
    empty_bytes_models = await BytesModel.afind()

    # Assert
    assert len(found_str_models) == 3
    for model in str_models:
        assert model in found_str_models

    assert len(found_int_models) == 2
    for model in int_models:
        assert model in found_int_models

    assert len(found_bool_models) == 4
    for model in bool_models:
        assert model in found_bool_models

    assert another_str_model not in found_str_models
    assert empty_bytes_models == []
