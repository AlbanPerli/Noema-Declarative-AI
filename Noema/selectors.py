from .Generator import Generator
from .Subject import Subject
from guidance import select

class Select(Generator):
    
    hint = "Response format: select the best option"
    
    def execute(self):
        llm = Subject().shared().llm
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
        Subject().shared().llm += display_var + " " + res + "\n"
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        Subject().shared().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if Subject().shared().verbose:
            print(f"{var} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint} : {self.options})'}\033[0m)")
            
            
class SelectOrNone(Generator):
    
    hint = "Response format: select the best option or 'None'"
    
    def execute(self):
        if "None" not in self.options:
            self.options.append("None")
        llm = Subject().shared().llm
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
        Subject().shared().llm += display_var + " " + res + "\n"
        self.noema = self.value
        if res == "None":
            self.value = None
        else:
            self.value = res
        self.noesis = noesis
        Subject().shared().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if Subject().shared().verbose:
            print(f"{var} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint} : {self.options})'}\033[0m)")
        