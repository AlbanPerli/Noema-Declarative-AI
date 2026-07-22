from .Generator import Generator
from .llm import current_runtime
from guidance import gen

class CodeGenerator(Generator):
    regex = None
    hint = "Response format: code"
    return_type = str

    def execute(self, max_tokens=500):
        print("Code Gen Value: ", self.value)
        runtime = current_runtime()
        llm = runtime.llm
        noesis = ""
        if self.hint != None:
            noesis = self.value + f"({self.hint})" + "\n"
        else:
            noesis = self.value + "\n"
        display_var = "#"+self.id.replace("self.", "").upper()+":"
        llm += noesis
        llm += " Produce only the code, no example or explanation." + "\n"  
        llm += runtime.reasoning_prelude()
        llm += display_var + " " + f" ```{self.__class__.__name__}\n" + gen(
            stop="```",
            name="response",
            **runtime.generation_kwargs(max_tokens),
        ) + "\n"
        res = llm["response"]
        runtime.llm = llm
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        self._record_automaton_value()
        if runtime.verbose:
            print(f"{self.id.replace('self.', '')} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint})'}\033[0m)")
