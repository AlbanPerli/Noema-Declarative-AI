import ast
from guidance import gen
from .Generator import Generator
from .Subject import Subject

class SemPy(Generator):
    hint = "Response format: A Python function."
    
    def __init__(self, value, max_retry=3):
        self.noesis = value
        self.instruction = value
        self.value = None
        self.max_retry = max_retry
        self.id = "Python_Code"
        
    def run(self, *args, **kwargs):
        local_context = {}
        print("Value: ", self.value)
        tree = ast.parse(self.value)

        func_name = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):  
                func_name = node.name
                
        exec(self.value, local_context)
        
        print("Function name: ", func_name)
        print("Args: ", args)
        result = local_context[func_name](*args)
        return result

    def format_parameters(self, args, kwargs):
        # Formatter args
        formatted_args = ", ".join(repr(arg) for arg in args)
        
        # Formatter kwargs
        formatted_kwargs = ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
        
        # Combiner args et kwargs
        if formatted_args and formatted_kwargs:
            return f"{formatted_args}, {formatted_kwargs}"
        elif formatted_args:
            return formatted_args
        elif formatted_kwargs:
            return formatted_kwargs
        else:
            return ""
        
    def __call__(self, *args, **kwargs):
        formated_params = self.format_parameters(args, kwargs)
        llm = Subject().shared().llm
        llm += f"""[INST]Generate a Python function to perform the following task:
{self.instruction}

Using the following form: 
```
import needed_libraries

def function_name({formated_params}):```

Produce only the code, no example or explanation.
[/INST]

```Python
"""

        llm += gen(name="response", stop="```")
        function_str = llm["response"]
        self.noema = function_str
        tree = ast.parse(function_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):  
                node.name = "noema_func"
                break
            
        function_str = ast.unparse(tree)
        local_context = {}
        print(function_str)
        exec(function_str, local_context)
        self.value = local_context["noema_func"](*args, **kwargs)
        if Subject().shared().verbose:
            print(f"\033[93m{self.noema}\n Returns:\n{self.value}\nFor parametters:{formated_params}\033[0m\n(\033[94m{self.noesis + f'({self.hint})'}\033[0m)")
        return self
        
        
        