import re
from .step import Step

class Write(Step):
    
    def __init__(self, value:str, var_name:str, extend:bool = False, action=None):
        if not re.match(r'\{(\w+)\}', var_name) and not re.match(r'\{\{(\w+)\}\}', var_name):
                raise ValueError(f"La source de donnée {var_name} doit être une variable entre accolades.")
        unwrapped_var_name = re.findall(r'\{(\w+)\}', var_name)[0]
        super().__init__(name=unwrapped_var_name, action=action)
        self.value = value
        self.extend = extend

    def execute(self, state):
        current_value = self.extract_variables_from_string(self.value, state)
        state.set(self.name, current_value, self.extend)
        return current_value
    
    def list_steps(self, state):
         return []
    
    def should_include_in_list(self):
         return False

class Clear(Step):
    
    def __init__(self, var_name:str, action=None):
        if not re.match(r'\{(\w+)\}', var_name) and not re.match(r'\{\{(\w+)\}\}', var_name):
                raise ValueError(f"La source de donnée {var_name} doit être une variable entre accolades.")
        unwrapped_var_name = re.findall(r'\{(\w+)\}', var_name)[0]
        super().__init__(name=unwrapped_var_name, action=action)
        
    def execute(self, state):
        state.set(self.name, None)
    
    def list_steps(self, state):
         return []
     
    def should_include_in_list(self):
         return False
    
class Add(Step):
    
    def __init__(self, value, var_name:str, action=None):
        if not re.match(r'\{(\w+)\}', var_name) and not re.match(r'\{\{(\w+)\}\}', var_name):
                raise ValueError(f"The datasource {var_name} must be a variable between curly braces.")
        unwrapped_var_name = re.findall(r'\{(\w+)\}', var_name)[0]
        super().__init__(name=unwrapped_var_name, action=action)
        self.value = value
        
    def execute(self, state):
        current_value = state.get(self.name, 0)
        state.set(self.name, current_value + self.value)
    
    def list_steps(self, state):
         return []
     
    def should_include_in_list(self):
         return False