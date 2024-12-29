from .Generator import Generator
from .Subject import Subject

class Information(Generator):
    
    def execute(self):
        display_var = "#"+self.id.replace("self.", "").upper()+":"
        noesis = display_var + " " + self.value + "\n"
        Subject().shared().llm += noesis
        self.value = self.value
        self.noema = self.value
        self.noesis = noesis
        Subject().shared().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if Subject().shared().verbose:
            print(f"{self.id.replace('self.', '')} = \033[94m{self.noema + f'({self.hint})'}\033[0m")
        