from .BaseGenerator import BaseGenerator
from .Generator import noema_generator
from .generation import execute_json_object


@noema_generator
class JsonObject(BaseGenerator):
    return_type = dict
    hint = "Response format: valid JSON object matching schema"

    def __init__(
        self,
        value=None,
        schema=None,
        idx: int = None,
        var: str = None,
        max_tokens: int | None = None,
    ):
        super().__init__()
        self.value = value
        self.schema = schema or {"type": "object"}
        self.idx = idx
        self.var = var
        self.max_tokens = max_tokens

    def execute(self, max_tokens=None):
        execute_json_object(self, max_tokens=max_tokens or self.max_tokens)
