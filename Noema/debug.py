import re
from .step import DebugStep, Step


class Print(DebugStep):
    def __init__(self, value):
        super().__init__("Print")
        self.value = value

    def execute(self, state):
        if isinstance(self.value, str):
            extracted = self.extract_variables_from_string(self.value, state)
            print(extracted)
        elif isinstance(self.value, Step):
            extracted = self.value.execute(state)
            print(extracted)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")

    def list_steps(self,state):
        return []
    
    def should_include_in_list(self):
         return False
     
     
     
class PrintNoema(DebugStep):
    def __init__(self):
        super().__init__("PrintNoema")

    def execute(self, state):
        BLUE = "\033[94m"
        RESET = "\033[0m"
        print(f"{BLUE}{state.noema}{RESET}")
        
    def list_steps(self,state):
        return []
    
    def should_include_in_list(self):
         return False
     
class PrintNoesis(DebugStep):
    def __init__(self):
        super().__init__("PrintNoema")

    def execute(self, state):
        YELLOW = "\033[93m"
        RESET = "\033[0m"
        print(f"{YELLOW}{state.noesis}{RESET}")
        
    def list_steps(self,state):
        return []
    
    def should_include_in_list(self):
         return False