from .Generator import Generator
from .llm import current_runtime
from guidance import gen

class Sentence(Generator):
    regex = None
    hint = "Response format: one sentence. Stop after the final punctuation"
    return_type = str
    stops = ["\n", "#"]
    max_tokens = 36
    
class Paragraph(Generator):
    regex = None
    hint = "Response format: one concise paragraph. Do not repeat phrases"
    return_type = str
    stops = ["\n", "#"]
    max_tokens = 120
    
class Free(Generator):
    regex = ""
    hint = "Response format: text"
    return_type = str
    max_tokens = 500
    
    def execute(self, max_tokens=None):
        max_tokens = max_tokens or self.max_tokens
        runtime = current_runtime()
        llm = runtime.llm
        noesis = ""
        if self.hint != None:
            noesis = self.value + f"({self.hint})" + "\n"
        else:
            noesis = self.value + "\n"
        display_var = "#"+self.id.replace("self.", "").upper()+":"
        llm += noesis
        llm += runtime.reasoning_prelude()
        llm += display_var + " " + gen(name="response", **runtime.generation_kwargs(max_tokens)) + "\n"
        res = llm["response"]
        runtime.llm = llm
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        runtime.append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if runtime.verbose:
            print(f"{self.id.replace('self.', '')} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint})'}\033[0m)")
