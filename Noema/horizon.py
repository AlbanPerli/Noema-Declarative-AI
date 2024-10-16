from .step import FlowStep, GenStep
from .var import Var


class Horizon:
    def __init__(self, *steps):
        self.steps = steps  

    def list_all_steps(self,state):
        step_names = []
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def list_steps(self,state):
        step_names = []
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names
    
    # T0D0: Build modular noesis
    def buildNoesis(self,state):
        for step in self.steps:
            if isinstance(step, Var):
                step.execute(state,False)
        noesisSteps = "\n".join(self.list_all_steps(state))
        noesis = f"""<s>[INST]You are functioning in a loop of thought. Here is your reasoning step by step:
{noesisSteps}
[/INST]
Here is the result of the reasoning:
"""
        return noesis
    
    
    def extract_noema(self,noema, noesis):
        noesis = noesis.replace("<s>","").replace("[/INST]","").replace("[INST]","")
        return f"{noesis} {noema}"
    
    def constituteWith(self, state):
        noesis = self.buildNoesis(state)
        noema = ""
        state.llm += noesis
        for step in self.steps:
            if isinstance(step, FlowStep):
                output = step.execute(state)
                noema += step.name + "\n"
                if output is not None:
                    break
            else:
                output = step.execute(state)
                if isinstance(step, GenStep):
                    noema += step.display_step_name + str(output) + "\n"
                else:
                    noema += step.name + "\n"
        state.noema += self.extract_noema(noema,noesis)
        return state


