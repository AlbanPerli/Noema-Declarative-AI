from .Generator import Generator
from .Subject import Subject
from guidance import gen

class CodeGenerator(Generator):
    regex = None
    hint = "Response format: code"
    return_type = str

    def execute(self, max_tokens=500):
        print("Code Gen Value: ", self.value)
        llm = Subject().shared().llm
        noesis = ""
        if self.hint != None:
            noesis = self.value + f"({self.hint})" + "\n"
        else:
            noesis = self.value + "\n"
        display_var = "#"+self.id.replace("self.", "").upper()+":"
        llm += noesis
        llm += " Produce only the code, no example or explanation." + "\n"  
        llm += display_var + " " + f" ```{self.__class__.__name__}\n" + gen(stop="```",name="response") + "\n"
        res = llm["response"]
        Subject().shared().llm += display_var + " " + res + "\n"
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        if Subject().shared().verbose:
            print(f"{self.id.replace('self.', '')} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint})'}\033[0m)")
