from .Generator import Generator, noema_generator
from .Subject import Subject
from guidance import substring


class Substring(Generator):
    
    hint = "Response format: extract a substring"
    
    def execute(self):
        llm = Subject().shared().llm
        noesis = ""
        if self.hint != None:
            noesis = self.value + f"({self.hint})" + "\n"
        else:
            noesis = self.value + "\n"
        display_var = "#"+self.id.replace("self.", "").upper()+":"
        llm += noesis
        llm += display_var + " " + substring(self.value, name='response') + "\n"
        res = llm["response"]
        Subject().shared().llm += display_var + " " + res + "\n"
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        Subject().shared().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if Subject().shared().verbose:
            print(f"{self.id.replace('self.', '')} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint})'}\033[0m)")
