import re
from .step import Step
from .noesis import Constitute, Noesis
from .execFunction import CallFunction

class Var(Step):
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        super().__init__(dest)
        self.value = value
        self.dest = dest
    
    def to_function(self, value):
        return lambda: value    
    
    def execute(self, state, run_step = True):
        value = self.value
        if isinstance(self.value, str):
            value = self.extract_variables_from_string(self.value, state, can_be_None=not run_step)
        elif isinstance(self.value, Noesis):
            value = self.value.execute(state)
        elif callable(self.value):
            if run_step:
                value = self.value()
            else:
                value = self.value
                
        return value

    def should_include_in_list(self):
        if isinstance(self.value, Constitute) or isinstance(self.value, CallFunction):
            return True
        else:
            return False
     
    def list_steps(self,state):
        if isinstance(self.value, CallFunction):
            return [f"Call function '{self.value.name}' with arg {self.value.args} and store the result in '{self.dest}'"]
        if isinstance(self.value,Constitute):
            return [f"Call function '{self.value.name}' with arg {self.value.args} and store the result in '{self.dest}'"]
        else:
            return []