import re
import time

from .returnStep import Return
from .step import GenStep, Step,FlowStep

class Noesis(Step):
    def __init__(self, name, param_names, steps, noema_name:str = "last_noema"):
        super().__init__(name)
        self.param_names = param_names
        self.steps = steps  
        self.current_args = None 
        self.noema_name = noema_name

    def list_steps(self, state):
        if self.current_args:
            param_str = ', '.join(f"{name}={arg}" for name, arg in zip(self.param_names, self.current_args))
            step_names = [f"{self.name} (Function with params: {param_str})"]
        else:
            param_str = ', '.join(f"#{name.upper()}" for name in self.param_names)
            step_names = [f"{self.name} (Function with params: {param_str})"]
        
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def describe(self):
        if self.current_args:
            return f"{self.name} (Function with params: {', '.join(f'{name}={arg}' for name, arg in zip(self.param_names, self.current_args))})"
        return f"{self.name} (Function with params: {', '.join(self.param_names)})"


    def buildNoesis(self, param_names, param_values, state):    
        param_list = [f"#{name.upper()}: {value}" for name, value in zip(param_names, param_values)]
        param_str = '\n'.join(param_list)
        nStep = self.list_steps(state)
        noesisSteps = "\n".join(nStep[1:])
        noesis = f"""<s>[INST]You are functioning in a loop of thought. Here is your reasoning step by step:
{noesisSteps}
[/INST]
Here is the result of the reasoning:
{param_str}
"""
        return noesis

    def execute_with_params(self, state, param_values, noesis_name):
        start_time = time.time()
        state.enter_namespace(f"{self.name}_params")
        for i, param_name in enumerate(self.param_names):
            param_value = param_values[i]
            state.set(param_name, param_value)

        current_noesis = self.buildNoesis(self.param_names, param_values, state)
        noema = current_noesis
        tmp_copy = str(state.llm)
        state.llm.reset()
        state.llm += "\n"+ current_noesis
        output = None
        for step in self.steps:
            if isinstance(step, Return):
                output = step.execute(state)
                print("IN RETURN")
                break
            elif isinstance(step, FlowStep):
                output = step.execute(state)
                if output is not None:
                    break
            else:
                output = step.execute(state)
                if isinstance(step, GenStep):
                    noema += step.display_step_name + str(output) + "\n"
                else:
                    noema += step.name + "\n"
        state.exit_namespace()
        
        end_time = time.time()
        duration = time.strftime("%M:%S", time.gmtime(end_time - start_time))
        print(f"Duration for '{self.name}' : {duration}s")
        state.set(self.noema_name, self.prepare_noema(noema))
        state.llm.reset()
        state.llm += tmp_copy
        return output

    # TODO: better way to prepare the noema
    def prepare_noema(self,noema:str):
        noema = noema.split("\n", 1)[1]
        noema = noema.replace(f"[INST]<s>[INST]You are functioning in a loop of thought. Here is your reasoning step by step:\n", "")
        noema = noema.replace("[/INST]", "")
        noema = noema.replace("<s>", "")
        noema = f"Objectif: {self.name}\n{noema}"
        return noema

    def resolve_param(self, param, state):
        if isinstance(param, str):
            return state.get(param)
        elif isinstance(param, Step):
            return param.execute(state)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")

class StepWrapper(Step):
    def __init__(self, name, func):
        super().__init__(name)
        self.func = func

    def execute(self, state):
        self.func(state)
        
        
class Constitute(Step):
    
    def __init__(self, function: Noesis, args: any, action=None):
        function_name = function.name
        super().__init__(name=function_name, action=action)
        
        self.function = function
        self.args = args if isinstance(args, tuple) else (args,)

        
    def resolve_param(self, param, state):
        if isinstance(param, str):
            if not re.match(r'\{(\w+)\}', param):
                return param
            else:
                unwrapped_param = self.extract_variables_from_string(param, state)
                return state.get(unwrapped_param)
        elif isinstance(param, Step):
            return param.execute(state)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        
    def execute(self, state, run_step = True):
        resolved_args = [self.resolve_param(arg, state) for arg in self.args]
        output = self.function.execute_with_params(state, resolved_args,self.name)
        state.llm += f"Result of '{self.name}' is: {output}"+ "\n"
        state.set(self.name, output)
        return output