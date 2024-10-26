from .step import Step

class Information(Step):
    
    def __init__(self, value:str):
        super().__init__(name="Information")
        self.value = value
        
    def execute(self, state):
        
        if isinstance(self.value, str):
            current_value = self.extract_variables_from_string(self.value, state)
        elif isinstance(self.value, Step):
            current_value = self.value.execute(state)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        state.llm += "#"+self.name.upper()+":"+ current_value + "\n"
        return current_value
    
    def list_steps(self,state):
        return ["#"+self.name.upper()+": "+self.value] if self.should_include_in_list() else []
