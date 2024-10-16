import re
from .step import Step

class CallFunction(Step):
    
    def __init__(self, function: callable, args: any, action=None):
        super().__init__(name=function.__name__, action=action)
        self.function = function
        self.args = args if isinstance(args, tuple) else (args,)

        
    def resolve_param(self, param, state):
        if isinstance(param, str):
            if not re.match(r'\{(\w+)\}', param):
                return param
            else:
                unwrapped_param = re.findall(r'\{(\w+)\}', param)[0]
                return state.get(unwrapped_param)
        elif isinstance(param, Step):
            return param.execute(state)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        
    def execute(self, state):
        resolved_args = [self.resolve_param(arg, state) for arg in self.args]
        return self.function(*resolved_args)

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