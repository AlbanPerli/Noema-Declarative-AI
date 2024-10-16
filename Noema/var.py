import re
from .step import Step
from .noesis import Constitute
from .execFunction import CallFunction

class Var(Step):
    def __init__(self, value = [], name:str=None):
        super().__init__(name)
        self.value = value
        self.dest = name
        if not re.match(r'\{(\w+)\}', self.dest):
            raise ValueError("The variable name must be in the form {varName}")
        
    def execute(self, state, run_step = True):
        unwrapped_var_name = self.dest
        if re.match(r'\{(\w+)\}', self.dest):
            unwrapped_var_name = re.findall(r'\{(\w+)\}', unwrapped_var_name)[0]
            
        if isinstance(self.value, str):
            var = self.extract_variables_from_string(self.value, state)
            state.set(unwrapped_var_name, var)
        elif isinstance(self.value, Step):
            if run_step:
                state.set(unwrapped_var_name, self.value.execute(state))
            else:
                state.set(unwrapped_var_name, self.value.name)
        elif self.value is None:
            return unwrapped_var_name
        else:
           state.set(unwrapped_var_name, self.value)
           
        return unwrapped_var_name

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