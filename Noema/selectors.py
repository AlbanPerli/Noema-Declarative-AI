from .Generator import Generator
from .llm import current_runtime
from guidance import select

class Select(Generator):
    
    hint = "Response format: select the best option"
    
    def execute(self):
        if not self.options:
            raise ValueError("Select requires at least one option.")
        llm = current_runtime().llm
        noesis = ""
        if self.hint != None:
            noesis = self.value + f"({self.hint})" + "\n"
        else:
            noesis = self.value + "\n"
            
        var = "" 
        display_var = ""
        if self.idx != None:
            var = self.id.replace("self.", "").upper()+f"_{self.idx}"
        else:
            var = self.id.replace("self.", "").upper()
        display_var = "#"+f"{var}:"
        llm += noesis 
        llm += display_var + " " + select(self.options,name='response') + "\n"
        res = llm["response"]
        current_runtime().llm = llm
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        current_runtime().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if current_runtime().verbose:
            print(f"{var} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint} : {self.options})'}\033[0m)")
            
            
class SelectOrNone(Generator):
    
    hint = "Response format: select the best option or 'None'"
    
    def execute(self):
        options = list(self.options or [])
        if "None" not in options:
            options.append("None")
        llm = current_runtime().llm
        noesis = ""
        if self.hint != None:
            noesis = self.value + f"({self.hint})" + "\n"
        else:
            noesis = self.value + "\n"
            
        var = "" 
        display_var = ""
        if self.idx != None:
            var = self.id.replace("self.", "").upper()+f"_{self.idx}"
        else:
            var = self.id.replace("self.", "").upper()
        display_var = "#"+f"{var}:"
        llm += noesis 
        llm += display_var + " " + select(options,name='response') + "\n"
        res = llm["response"]
        current_runtime().llm = llm
        self.noema = self.value
        if res == "None":
            self.value = None
        else:
            self.value = res
        self.noesis = noesis
        current_runtime().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if current_runtime().verbose:
            print(f"{var} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint} : {options})'}\033[0m)")
        
