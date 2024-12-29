from .BaseGenerator import BaseGenerator
from guidance import gen, select, substring
from .Subject import Subject
from varname import varname

def noema_generator(cls):
    class Wrapped(cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            original_class_type = self.__class__
            self.id = varname()
            self.id = self.id.replace("self.", "")
            if hasattr(self, 'var') and self.var is not None:
                self._value = f"#{self.var.upper()}:"
            elif hasattr(self, 'value') and self.value is not None:
                self.execute()

        def __str__(self):
            return self._value if hasattr(self, '_value') else super().__str__()
    return Wrapped

@noema_generator
class Generator(BaseGenerator):
    regex = None
    return_type = None
    hint = None
    stops = []
    
    def __init__(self, value=None, idx:int = None, var: str = None, options: list = None):
        super().__init__()
        self.var = var
        self.value = value
        self.idx = idx
        self.options = options
        
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
        
        if self.regex == "":
            llm += display_var + " " + gen(name="response") + "\n"
        else:
            llm += display_var + " " + gen(regex=self.regex, stop=self.stops, name="response") + "\n"
        res = llm["response"]
        Subject().shared().llm += display_var + " " + res + "\n"
        self.noema = self.value
        if self.return_type == bool:
            self.value = True if res == "True" else False
        else:
            self.value = self.return_type(res)
        self.noesis = noesis
        Subject().shared().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if Subject().shared().verbose:
            print(f"{var} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint})'}\033[0m)")    



# TODO: Implement Fill class
# class Fill(Generator):
#     regex = ""
    
#     def __init__(self, header, body, value=None):
#         super().__init__(value)
#         self.header = header
#         self.body = body


