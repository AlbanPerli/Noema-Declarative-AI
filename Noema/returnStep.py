from .step import Step

class Return(Step):
    def __init__(self, value):
        super().__init__("Return")
        self.value = value

    def execute(self, state):
        return self.extract_variables_from_string(self.value, state)
    
    def list_steps(self, state):
        return []
    
    def should_include_in_list(self):
        return False
        