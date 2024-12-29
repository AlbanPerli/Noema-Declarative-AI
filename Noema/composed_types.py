import varname
from .BaseGenerator import BaseGenerator
from .Generator import noema_generator
from .Subject import Subject
from guidance import gen, select

@noema_generator
class ListOf(BaseGenerator):
    regex = None
    return_type = list
    hint = "Response format: a list of #ITEM_TYPE# separated by carriage returns."
    stops = []
    
    def __init__(self, type=None, value=None, idx:int = None, var: str = None):
        super().__init__()
        self.type = type
        self.var = var
        self.value = value
        self.idx = idx
        
    def execute(self):
        llm = Subject().shared().llm
        noesis = ""
        local_hint = ""
        if self.hint != None:
            local_hint = self.hint.replace("#ITEM_TYPE#", self.type.__name__)
            noesis = self.value + f"({local_hint})" + "\n"
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
        
        item = self.type()
        res = []
        llm += display_var + "\n```\n"
        first = True
        for i in range(100):
            if first:
                llm += f"{i+1}. " + gen(name="response", regex=item.regex, stop=f"\n{i+2}.") + "\n"
                value = llm["response"].strip()
                first = False
            else:
                llm += select([f"{i+1}. " + gen(name="response", regex=item.regex, stop=f"\n{i+2}.") + "\n", "```"], name="selected")
                value = llm["selected"].strip()
            if value == "```":
                break
            value = value.replace(f"{i+1}. ", "", 1)
            res.append(value)
            
        res_str = "\n".join(res)
        Subject().shared().llm += display_var + " " + res_str + "\n"
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        Subject().shared().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if Subject().shared().verbose:
            print(f"{var} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({local_hint})'}\033[0m)")    
