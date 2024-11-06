from .step import DebugStep, FlowStep, GenStep, ReflexiveStep
from .subject import Subject
from .var import Var


class Horizon:
    def __init__(self, *steps):
        self.steps = steps  

    def list_all_steps(self,state):
        step_names = []
        for step in self.steps:
            if not isinstance(step, DebugStep) and not isinstance(step,FlowStep):
                state.set_prop(step.name,None)
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
    
    def build_noema(self,noema_inst, noema_prod):
        return f"""{noema_inst}
Here is the result of the reasoning:
{noema_prod}
"""
    
    def constituteWith(self, state):
        noesis = self.buildNoesis(state)
        state.llm += noesis
        for step in self.steps:
            output = step.execute(state)
            if isinstance(step, GenStep) and not isinstance(step, ReflexiveStep):
                state.update_noesis(step.display_step_name + str(step.current_llm_input))
                state.update_noema(step.display_step_name + str(output))
                
            if not isinstance(step, DebugStep) and not isinstance(step,FlowStep):
                state.set_prop(step.name,output)
                
        return state


