from .Generator import Generator
from .llm import current_runtime

class Information(Generator):
    
    def execute(self):
        display_var = "#"+self.id.replace("self.", "").upper()+":"
        noesis = display_var + " " + self.value + "\n"
        current_runtime().llm += noesis
        self.value = self.value
        self.noema = self.value
        self.noesis = noesis
        current_runtime().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if current_runtime().verbose:
            hint = f"({self.hint})" if self.hint is not None else ""
            print(f"{self.id.replace('self.', '')} = \033[94m{self.noema}{hint}\033[0m")
        
