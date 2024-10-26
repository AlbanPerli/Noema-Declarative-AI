from .memoryFragment import *
import inspect
from typing import get_origin, get_args

class ExecutableMemoryFragment(MemoryFragment):
    def __init__(self, text, subject, metadata, distance=None):
        super().__init__(text, subject, metadata, distance)

    def is_runnable(self):
        return self.subject == 'function'

    def validate_type(self, arg, expected_type):
        origin = get_origin(expected_type)
        args = get_args(expected_type)

        if origin is not None:
            if origin is list:
                if not isinstance(arg, list):
                    raise TypeError(f"Expected {origin}, but received {type(arg)} with value {arg}")
                if args:
                    for index, item in enumerate(arg):
                        print(f"Validating element {index} of {arg} against {args[0]}")
                        try:
                            self.validate_type(item, args[0])
                        except TypeError as e:
                            raise TypeError(f"Element {index} of {arg} is not of type {args[0]}: {e}")
            else:
                if not isinstance(arg, expected_type):
                    raise TypeError(f"Expected {origin}, but received {type(arg)} with value {arg}")
        else:
            if isinstance(expected_type, type):
                if not isinstance(arg, expected_type):
                    raise TypeError(f"Expected {expected_type}, but received {type(arg)} with value {arg}")
            else:
                raise TypeError(f"Expected {expected_type}, but received {type(arg)} with value {arg}")

    def validate_function_signature(self, func, args):
        try:
            sig = inspect.signature(func)
        except ValueError as e:
            raise RuntimeError(f"Unable to get signature of function: {str(e)}")

        params = sig.parameters
        print(f"Function: {func}")
        print(f"Signature: {sig}")
        print(f"Params: {params}")
        print(f"Args: {args}")
        if len(args) != len(params):
            raise TypeError(f"Expected {len(params)} arguments, but received {len(args)}")
        

        for i, (name, param) in enumerate(params.items()):
            if i < len(args):  
                expected_type = param.annotation
                if expected_type != param.empty:
                    self.validate_type(args[i], expected_type)
        
        return True

    def __call__(self, args):
        if not self.is_runnable():
            raise ValueError("Le fragment de mémoire n'est pas exécutable")

        local_namespace = {}

        try:
            scope = self.metadata["scope"]
            strCode = ""
            if scope != 'global':
                local_namespace[scope] = __import__(scope)
                strCode = f"from {scope} import *\n"+self.value
            else:
                strCode = self.value
            local_namespace['pendulum'] = __import__('pendulum')
            
            exec(strCode, local_namespace)
            
            func_name = self.value.split('def ')[1].split('(')[0].strip()

            func = local_namespace.get(func_name)
            if func is None:
                raise ValueError("No function found in the memory fragment")

            if self.validate_function_signature(func, args): 
                result = func(*args)
                return result

            return "Execution successful"

        except Exception as e:
            raise RuntimeError(f"Error while executing memory fragment: {str(e)}")
