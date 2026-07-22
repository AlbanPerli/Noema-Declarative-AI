from .Generator import Generator, noema_generator
from .llm import current_runtime
from guidance import substring


class Substring(Generator):
    
    hint = "Response format: extract a substring"
    
    def execute(self):
        llm = current_runtime().llm
        noesis = ""
        if self.hint != None:
            noesis = self.value + f"({self.hint})" + "\n"
        else:
            noesis = self.value + "\n"
        display_var = "#"+self.id.replace("self.", "").upper()+":"
        llm += noesis
        llm += display_var + " " + substring(self.value, name='response') + "\n"
        res = llm["response"]
        current_runtime().llm = llm
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        current_runtime().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if current_runtime().verbose:
            print(f"{self.id.replace('self.', '')} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint})'}\033[0m)")
