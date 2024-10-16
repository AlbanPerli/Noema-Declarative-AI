import re
from Logos.step import Step


class Print(Step):
    def __init__(self, value):
        super().__init__("Print")
        self.value = value

    def execute(self, state):
        if isinstance(self.value, str):
            extracted = self.extract_variables_from_string(self.value, state)
            print("DEBUG:",extracted)
        elif isinstance(self.value, Step):
            extracted = self.value.execute(state)
            print("DEBUG:",extracted)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")

    def list_steps(self,state):
        return []
    
    def should_include_in_list(self):
         return False
     
     
     
class PrintNoema(Step):
    def __init__(self):
        super().__init__("Print")

    def execute(self, state):
        BLUE = "\033[94m"
        RESET = "\033[0m"
        print(f"{BLUE}{state.llm}{RESET}")
        
    def list_steps(self,state):
        return []
    
    def should_include_in_list(self):
         return False