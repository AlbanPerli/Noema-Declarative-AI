from .Generator import Generator
from .generation import execute_selection

class Select(Generator):
    
    hint = "Response format: select the best option"
    
    def execute(self):
        execute_selection(self)
            
            
class SelectOrNone(Generator):
    
    hint = "Response format: select the best option or 'None'"
    
    def execute(self):
        execute_selection(self, allow_none=True)
        
