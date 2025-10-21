import pytest
from typing import Optional, Union, Annotated, Any, Generic, TypeVar, TypeVarTuple
from rapyer.utils import replace_to_redis_types_in_annotation

T = TypeVar("T")
V = TypeVar("V")
Ts = TypeVarTuple("Ts")


class NewStr:
    pass


class NewInt:
    pass


class NewDict(Generic[T, V]):
    pass


class NewList(Generic[T]):
    pass


class NewTuple(Generic[*Ts]):
    pass


class NewBool:
    pass


class NewFloat:
    pass


@pytest.fixture
def type_mapping():
    return {
        str: NewStr,
        int: NewInt,
        dict: NewDict,
        list: NewList,
        tuple: NewTuple,
        bool: NewBool,
        float: NewFloat,
    }


@pytest.mark.parametrize(
    "original_type, expected_type",
    [
        (str, NewStr),
        (int, NewInt),
        (dict, NewDict),
        (list, NewList),
        (tuple, NewTuple),
        (bool, NewBool),
        (float, NewFloat),
    ],
)
def test_simple_type_replacement_sanity(type_mapping, original_type, expected_type):
    # Arrange
    # Act
    result = replace_to_redis_types_in_annotation(original_type, type_mapping)

    # Assert
    assert result == expected_type


def test_unmapped_type_unchanged_sanity(type_mapping):
    # Arrange
    unmapped_type = bytes

    # Act
    result = replace_to_redis_types_in_annotation(unmapped_type, type_mapping)

    # Assert
    assert result == bytes


@pytest.mark.parametrize(
    "optional_type, expected_inner_type",
    [
        (Optional[str], NewStr),
        (Optional[int], NewInt),
        (Optional[list], NewList),
    ],
)
def test_optional_type_replacement_sanity(
    type_mapping, optional_type, expected_inner_type
):
    # Arrange
    # Act
    result = replace_to_redis_types_in_annotation(optional_type, type_mapping)

    # Assert
    assert result == Optional[expected_inner_type]


@pytest.mark.parametrize(
    "union_type, expected_result",
    [
        (Union[str, int], Union[NewStr, NewInt]),
        (Union[str, int, bool], Union[NewStr, NewInt, NewBool]),
        (Union[str, bytes], Union[NewStr, bytes]),  # bytes unmapped
    ],
)
def test_union_type_replacement_sanity(type_mapping, union_type, expected_result):
    # Arrange
    # Act
    result = replace_to_redis_types_in_annotation(union_type, type_mapping)

    # Assert
    assert result == expected_result


def test_annotated_type_with_metadata_preservation_sanity(type_mapping):
    # Arrange
    metadata = "field documentation"
    annotated_type = Annotated[str, metadata]

    # Act
    result = replace_to_redis_types_in_annotation(annotated_type, type_mapping)

    # Assert
    assert result == Annotated[NewStr, metadata]


def test_annotated_optional_type_preservation_sanity(type_mapping):
    # Arrange
    metadata = "optional field"
    annotated_type = Annotated[Optional[str], metadata]

    # Act
    result = replace_to_redis_types_in_annotation(annotated_type, type_mapping)

    # Assert
    assert result == Annotated[Optional[NewStr], metadata]


@pytest.mark.parametrize(
    "generic_type, expected_result",
    [
        (list[str], NewList[NewStr]),
        (dict[str, int], NewDict[NewStr, NewInt]),
        (tuple[str, int], NewTuple[NewStr, NewInt]),
        (tuple[str, ...], NewTuple[NewStr, ...]),
    ],
)
def test_generic_type_replacement_sanity(type_mapping, generic_type, expected_result):
    # Arrange
    # Act
    result = replace_to_redis_types_in_annotation(generic_type, type_mapping)

    # Assert
    assert result == expected_result


@pytest.mark.parametrize(
    ["nested_type","expected_result"],
    [
        (dict[str, list[int]], NewDict[NewStr, NewList[NewInt]]),
        (list[dict[str, int]], NewList[NewDict[NewStr, NewInt]]),
        (tuple[str, dict[int, list]], NewTuple[NewStr, NewDict[NewInt, NewList]]),
        (Optional[dict[str, list[int]]], Optional[NewDict[NewStr, NewList[NewInt]]]),
    ],
)
def test_nested_generic_type_replacement_sanity(
    type_mapping, nested_type, expected_result
):
    # Arrange
    # Act
    result = replace_to_redis_types_in_annotation(nested_type, type_mapping)

    # Assert
    assert result == expected_result


def test_complex_annotated_nested_type_replacement_sanity(type_mapping):
    # Arrange
    metadata = "complex field"
    complex_type = Annotated[Optional[tuple[str, dict[int, list]]], metadata]
    expected = Annotated[Optional[NewTuple[NewStr, NewDict[NewInt, NewList]]], metadata]

    # Act
    result = replace_to_redis_types_in_annotation(complex_type, type_mapping)

    # Assert
    assert result == expected


def test_deeply_nested_type_replacement_sanity(type_mapping):
    # Arrange
    deep_type = dict[str, dict[int, list[tuple[str, bool]]]]
    expected = NewDict[NewStr, NewDict[NewInt, NewList[NewTuple[NewStr, NewBool]]]]

    # Act
    result = replace_to_redis_types_in_annotation(deep_type, type_mapping)

    # Assert
    assert result == expected


def test_union_with_optional_replacement_sanity(type_mapping):
    # Arrange
    union_optional = Union[str, Optional[int], bool]
    expected = Union[NewStr, Optional[NewInt], NewBool]

    # Act
    result = replace_to_redis_types_in_annotation(union_optional, type_mapping)

    # Assert
    assert result == expected


def test_empty_type_mapping_unchanged_sanity():
    # Arrange
    empty_mapping = {}
    annotation = Optional[dict[str, list[int]]]

    # Act
    result = replace_to_redis_types_in_annotation(annotation, empty_mapping)

    # Assert
    assert result == annotation


def test_any_type_unchanged_sanity(type_mapping):
    # Arrange
    any_annotation = Any

    # Act
    result = replace_to_redis_types_in_annotation(any_annotation, type_mapping)

    # Assert
    assert result == Any


def test_multiple_annotations_with_same_metadata_sanity(type_mapping):
    # Arrange
    metadata1 = "first"
    metadata2 = "second"
    annotated_type = Annotated[str, metadata1, metadata2]
    expected = Annotated[NewStr, metadata1, metadata2]

    # Act
    result = replace_to_redis_types_in_annotation(annotated_type, type_mapping)

    # Assert
    assert result == expected


def test_nested_optional_with_union_replacement_sanity(type_mapping):
    # Arrange
    nested_complex = Optional[Union[str, dict[int, list[bool]]]]
    expected = Optional[Union[NewStr, NewDict[NewInt, NewList[NewBool]]]]

    # Act
    result = replace_to_redis_types_in_annotation(nested_complex, type_mapping)

    # Assert
    assert result == expected


def test_tuple_with_ellipsis_replacement_sanity(type_mapping):
    # Arrange
    tuple_ellipsis = tuple[str, ...]
    expected = NewTuple[NewStr, ...]

    # Act
    result = replace_to_redis_types_in_annotation(tuple_ellipsis, type_mapping)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    ["input_type", "expected_type"],
    [
        [
            Annotated[
                Optional[Union[str, dict[int, list[tuple[bool, float]]]]],
                "very complex",
            ],
            Annotated[
                Optional[Union[NewStr, NewDict[NewInt, NewList[NewTuple[NewBool, NewFloat]]]]],
                "very complex",
            ],
        ],
        [
            Union[Annotated[str, "doc1"], Annotated[int, "doc2"]],
            Union[Annotated[NewStr, "doc1"], Annotated[NewInt, "doc2"]],
        ],
    ],
)
def test_extremely_complex_type_scenarios_edge_case(type_mapping, input_type, expected_type):
    # Act
    result = replace_to_redis_types_in_annotation(input_type, type_mapping)

    # Assert
    assert result == expected_type


def test_pipe_union_in_generic_partial_replacement_edge_case(type_mapping):
    # Arrange
    pipe_union_generic = dict[str | int, list[Optional[bool]]]
    # bool gets replaced, pipe union doesn't
    expected = NewDict[NewStr | NewInt, NewList[Optional[NewBool]]]

    # Act
    result = replace_to_redis_types_in_annotation(pipe_union_generic, type_mapping)

    # Assert
    # The function replaces what it can (bool -> NewBool) but leaves pipe union unchanged
    assert result == expected


def test_recursive_type_with_none_values_edge_case(type_mapping):
    # Arrange
    type_with_none = Union[str, None, dict[int, Union[bool, None]]]
    expected = Union[NewStr, None, NewDict[NewInt, Union[NewBool, None]]]

    # Act
    result = replace_to_redis_types_in_annotation(type_with_none, type_mapping)

    # Assert
    assert result == expected


def test_annotated_none_type_edge_case(type_mapping):
    # Arrange
    annotated_none = Annotated[None, "nullable field"]

    # Act
    result = replace_to_redis_types_in_annotation(annotated_none, type_mapping)

    # Assert
    assert result == annotated_none  # None should remain unchanged


def test_partial_mapping_edge_case():
    # Arrange
    partial_mapping = {str: NewStr, int: NewInt}
    mixed_type = dict[str, list[bool]]  # bool not in mapping
    expected = dict[NewStr, list[bool]]  # only str gets replaced

    # Act
    result = replace_to_redis_types_in_annotation(mixed_type, partial_mapping)

    # Assert
    assert result == expected
