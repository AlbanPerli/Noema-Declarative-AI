import re
from .step import Step

class CallFunction(Step):
    
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        if not callable(value):
            raise ValueError("The parameter must be a lambda function containing the Noesis to call.")
        super().__init__(dest)
        self.value = value
        
    def execute(self, state):
        output = self.value()
        state.set_prop(self.name, output)
        return output


class WriteToFile(CallFunction):
    
    def __init__(self, content:str, file_path:str, append:bool = True, action=None):
        writingMode = 'w'
        if append:
            writingMode = 'a+'
        super().__init__("{WriteToFile}", open, (file_path, writingMode), action)
        self.content = content
        self.append = append
        
    def execute(self, state):
        resolved_params = [self.resolve_param(arg, state) for arg in self.args]
        file = self.function(*resolved_params)
        current_content = self.extract_variables_from_string(self.content,state)
        file.write(current_content+"\n")
        file.close()
        
    def list_steps(self, state):
        return [f"Write content to file {self.args[0]}: {self.content}"]