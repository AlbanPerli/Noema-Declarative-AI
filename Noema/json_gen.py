import json as json_module

from guidance import json as guidance_json

from .BaseGenerator import BaseGenerator
from .Generator import noema_generator
from .llm import current_runtime


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
        max_tokens = max_tokens or self.max_tokens
        runtime = current_runtime()
        llm = runtime.llm
        schema_text = json_module.dumps(self.schema, ensure_ascii=True)

        if self.hint is not None:
            noesis = self.value + f"({self.hint}: {schema_text})" + "\n"
        else:
            noesis = self.value + "\n"

        if self.idx is not None:
            var = self.id.replace("self.", "").upper() + f"_{self.idx}"
        else:
            var = self.id.replace("self.", "").upper()

        generation_kwargs = {}
        if max_tokens is not None:
            generation_kwargs["max_tokens"] = max_tokens
        temperature = getattr(runtime, "temperature", None)
        if temperature is not None:
            generation_kwargs["temperature"] = temperature

        llm += noesis
        llm += runtime.reasoning_prelude()
        llm += "#" + var + ": "
        llm += guidance_json(
            name="response",
            schema=self.schema,
            separators=(",", ": "),
            whitespace_flexible=True,
            **generation_kwargs,
        ) + "\n"

        raw_response = llm["response"]
        parsed = json_module.loads(str(raw_response))
        if not isinstance(parsed, dict):
            raise ValueError("JsonObject expected a JSON object.")

        runtime.llm = llm
        self.noema = self.value
        self.value = parsed
        self.noesis = noesis
        runtime.append_to_chain(
            {"value": self.value, "noema": self.noema, "noesis": self.noesis}
        )
        self._record_automaton_value()

        if getattr(runtime, "verbose", False):
            print(
                f"{var} = \033[93m{json_module.dumps(parsed, ensure_ascii=True)}\033[0m "
                f"(\033[94m{self.noema + f'({self.hint})'}\033[0m)"
            )
