from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union


class Expression:
    def create_filter(self) -> str:
        raise NotImplementedError("Subclasses must implement create_filter")

    def __and__(self, other: "Expression") -> "AndExpression":
        return AndExpression(self, other)

    def __or__(self, other: "Expression") -> "OrExpression":
        return OrExpression(self, other)

    def __invert__(self) -> "NotExpression":
        return NotExpression(self)


class ExpressionField(Expression):
    def __init__(self, field_name: str):
        self.field_name = field_name

    def create_filter(self) -> str:
        return f"@{self.field_name}:*"

    def __eq__(self, value: Any) -> "EqExpression":
        return EqExpression(self, value)

    def __ne__(self, value: Any) -> "NeExpression":
        return NeExpression(self, value)

    def __gt__(self, value: Any) -> "GtExpression":
        return GtExpression(self, value)

    def __lt__(self, value: Any) -> "LtExpression":
        return LtExpression(self, value)

    def __ge__(self, value: Any) -> "GteExpression":
        return GteExpression(self, value)

    def __le__(self, value: Any) -> "LteExpression":
        return LteExpression(self, value)


class EqExpression(Expression):
    def __init__(self, left: ExpressionField, right: Any):
        self.left = left
        self.right = right
        self.operation = "eq"

    def create_filter(self) -> str:
        # For string fields, wrap in quotes if needed
        if isinstance(self.right, str):
            # Escape special characters in the string
            escaped_value = (
                self.right.replace('"', '\\"').replace("\\", "\\\\").replace("/", "\\/")
            )
            return f'@{self.left.field_name}:"{escaped_value}"'
        # For numeric fields, use range syntax for exact match
        return f"@{self.left.field_name}:[{self.right} {self.right}]"


class NeExpression(Expression):
    def __init__(self, left: ExpressionField, right: Any):
        self.left = left
        self.right = right
        self.operation = "ne"

    def create_filter(self) -> str:
        # For not equal, we need to use different syntax
        if isinstance(self.right, str):
            escaped_value = (
                self.right.replace('"', '\\"').replace("\\", "\\\\").replace("/", "\\/")
            )
            return f'-@{self.left.field_name}:"{escaped_value}"'
        # For numeric fields, use range syntax for exact match
        return f"-@{self.left.field_name}:[{self.right} {self.right}]"


class GtExpression(Expression):
    def __init__(self, left: ExpressionField, right: Any):
        self.left = left
        self.right = right
        self.operation = "gt"

    def create_filter(self) -> str:
        return f"@{self.left.field_name}:[({self.right} +inf]"


class LtExpression(Expression):
    def __init__(self, left: ExpressionField, right: Any):
        self.left = left
        self.right = right
        self.operation = "lt"

    def create_filter(self) -> str:
        return f"@{self.left.field_name}:[-inf ({self.right}]"


class GteExpression(Expression):
    def __init__(self, left: ExpressionField, right: Any):
        self.left = left
        self.right = right
        self.operation = "gte"

    def create_filter(self) -> str:
        return f"@{self.left.field_name}:[{self.right} +inf]"


class LteExpression(Expression):
    def __init__(self, left: ExpressionField, right: Any):
        self.left = left
        self.right = right
        self.operation = "lte"

    def create_filter(self) -> str:
        return f"@{self.left.field_name}:[-inf {self.right}]"


class AndExpression(Expression):
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
        self.operation = "and"

    def create_filter(self) -> str:
        # In Redis Search, AND is implicit with space
        left_filter = self.left.create_filter()
        right_filter = self.right.create_filter()
        return f"({left_filter}) ({right_filter})"


class OrExpression(Expression):
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
        self.operation = "or"

    def create_filter(self) -> str:
        # In Redis Search, OR needs pipe operator
        left_filter = self.left.create_filter()
        right_filter = self.right.create_filter()
        return f"({left_filter})|({right_filter})"


class NotExpression(Expression):
    def __init__(self, expression: Expression):
        self.expression = expression
        self.operation = "not"

    def create_filter(self) -> str:
        # NOT operator in Redis Search
        inner_filter = self.expression.create_filter()
        return f"-{inner_filter}"
