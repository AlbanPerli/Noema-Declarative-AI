from .Generator import Generator
from .generation import execute_generation

class CodeGenerator(Generator):
    regex = None
    hint = "Response format: code"
    return_type = str

    def execute(self, max_tokens=500):
        execute_generation(
            self,
            max_tokens=max_tokens,
            stops="```",
            prefix=f"```{self.__class__.__name__}\n",
            extra_prompt="Produce only the code, no example or explanation.",
        )
