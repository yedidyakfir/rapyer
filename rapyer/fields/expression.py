from rapyer.fields.operators import Expression


class ExpressionField(Expression):
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def create_filter(self) -> str:
        return f"@{self.field_name}:*"
