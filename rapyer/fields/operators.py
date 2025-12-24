from typing import Any


class Expression:
    def __and__(self, other: "Expression") -> "AndExpression":
        return AndExpression(self, other)

    def __or__(self, other: "Expression") -> "OrExpression":
        return OrExpression(self, other)

    def __invert__(self) -> "NotExpression":
        return NotExpression(self)

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
    def __init__(self, left: Expression, right: Any):
        self.left = left
        self.right = right
        self.operation = "eq"


class NeExpression(Expression):
    def __init__(self, left: Expression, right: Any):
        self.left = left
        self.right = right
        self.operation = "ne"


class GtExpression(Expression):
    def __init__(self, left: Expression, right: Any):
        self.left = left
        self.right = right
        self.operation = "gt"


class LtExpression(Expression):
    def __init__(self, left: Expression, right: Any):
        self.left = left
        self.right = right
        self.operation = "lt"


class GteExpression(Expression):
    def __init__(self, left: Expression, right: Any):
        self.left = left
        self.right = right
        self.operation = "gte"


class LteExpression(Expression):
    def __init__(self, left: Expression, right: Any):
        self.left = left
        self.right = right
        self.operation = "lte"


class AndExpression(Expression):
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
        self.operation = "and"


class OrExpression(Expression):
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
        self.operation = "or"


class NotExpression(Expression):
    def __init__(self, expression: Expression):
        self.expression = expression
        self.operation = "not"
