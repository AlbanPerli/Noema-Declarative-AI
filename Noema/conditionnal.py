from .returnStep import Return
from .step import Step, FlowStep
from .var import *
from .subject import *

class IF(FlowStep):
    def __init__(self, condition, steps_if_true, ELSE=None):
        super().__init__("IF")
        self.condition = condition  
        self.steps_if_true = steps_if_true
        self.steps_if_false = ELSE or []
        self.condition_description = self._describe_condition()

    def _describe_condition(self):
        """Retourne une description lisible de la condition."""
        if isinstance(self.condition, str):
            return self.condition
        elif isinstance(self.condition, Step):
            return f"Condition Step: {self.condition.name}"
        else:
            return "Executable Condition"

    def list_steps(self,state):
        for step in self.steps_if_true:
            if isinstance(step, Var):
                step.execute(state,False)
        for step in self.steps_if_false:
            if isinstance(step, Var):
                step.execute(state,False)
                
        step_names = [f"{self.name} (Condition: {self.condition_description})"]
        step_names.append("  IF True:")
        for step in self.steps_if_true:
            step_names.extend(['    ' + sub_step for sub_step in step.list_steps(state)])
        if self.steps_if_false:
            step_names.append("  ELSE:")
            for step in self.steps_if_false:
                step_names.extend(['    ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def evaluate_condition(self, state):
        if callable(self.condition):
            try:
                return self.condition()
            except Exception as e:
                print(f"Error evaluating condition: {e}")
                return False
        elif isinstance(self.condition, Step):
            result = self.condition.execute(state)
            return bool(result)
        else:
            raise ValueError("Condition must be a lambda function or a Step instance")

    def execute(self, state):
        outputs = []
        prop_to_remove = []
        if self.evaluate_condition(state):
            for step in self.steps_if_true:
                if isinstance(step, Return):
                    for prop in prop_to_remove:
                        state.set_prop(prop,None)
                    return step.execute(state)
                else:
                    outputs.append(step.execute(state))
                    state.set_prop(step.name,outputs[-1])
                    prop_to_remove.append(step.name)
        else:
            for step in self.steps_if_false:
                if isinstance(step, Return):
                    for prop in prop_to_remove:
                        state.set_prop(prop,None)
                    return step.execute(state)
                else:
                    outputs.append(step.execute(state))
                    state.set_prop(step.name,outputs[-1])
                    prop_to_remove.append(step.name)
          
        # TODO: think about the variable scope. Should we remove the variables created in the IF block?          
        # for prop in prop_to_remove:
        #     state.set_prop(prop,None)