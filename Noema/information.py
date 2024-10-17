from .step import Step

class Information(Step):
    
    def __init__(self, value:str, action=None):
        super().__init__(name="Information: ", action=action)
        self.value = value
        
    def execute(self, state):
        
        if isinstance(self.value, str):
            current_value = self.extract_variables_from_string(self.value, state)
            state.llm += current_value + "\n"
        elif isinstance(self.value, Step):
            current_value = self.value.execute(state)
            state.llm += current_value + "\n"
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        
        return current_value
    
    def list_steps(self,state):
        return [self.name+" "+self.value] if self.should_include_in_list() else []
