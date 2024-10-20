from .var import Var
from .step import *
from .subject import *

class Repeat(Step):
    def __init__(self, count, steps):
        super().__init__("Repeat")
        self.count = count  
        self.steps = steps
        
    def list_steps(self,state):
        step_names = [f"{self.name} (x{self.count})"]
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def get_count(self, state):
        if isinstance(self.count, int):
            return self.count
        elif isinstance(self.count, Step):
            count = self.count.execute(state)
            if not isinstance(count, int):
                raise ValueError("The Step must return an integer.")
            return count
        elif callable(self.count):
            count = self.count()
            if not isinstance(count, int):
                raise ValueError("The function must return an integer.")
            return count
        else:
            raise ValueError("The count must be either an integer, a Step that returns an integer or a function that returns an integer.")

    def execute(self, state):
        repetitions = self.get_count(state)
        noema = ""
        for i in range(repetitions):
            for step in self.steps:
                output = step.execute(state)
                if isinstance(step, GenStep):
                    noema += step.display_step_name + str(output) + "\n"                
                else:
                    noema += step.name + "\n"
                    
                if not isinstance(step, DebugStep) and not isinstance(step,FlowStep):
                    state.set_prop(step.name,output)
                
class ForEach(Step):
    def __init__(self, source, steps):
        super().__init__("Foreach")
        self.source = None
        if callable(source):
            self.source = source
        elif isinstance(source, list):
            self.source = source  

        self.steps = steps
        self.source_description = self._describe_source()

    def _describe_source(self):
        if isinstance(self.source, str):
            return f"State key: {self.source}"
        elif isinstance(self.source, Step):
            return f"Step: {self.source.name}"
        else:
            return "Unknown Source"

    def list_steps(self,state):
        for step in self.steps:
            if isinstance(step, Var):
                step.execute(state,False)
        step_names = [f"{self.name} (Source: {self.source_description}, Item: item, Counter: idx)"]
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def execute(self, state):
        items = self.get_items(state)
        noema = ""
        for index, item in enumerate(items):
            state.set_prop("item", item)
            state.set_prop("idx" , index+1)
            
            for step in self.steps:
                output = step.execute(state)
                if isinstance(step, GenStep):
                    noema += step.display_step_name + str(output) + "\n"                
                else:
                    noema += step.name + "\n"
                    
                if not isinstance(step, DebugStep) and not isinstance(step,FlowStep):
                    state.set_prop(step.name,output)

        state.set_prop("item", None)
        state.set_prop("idx" , None)
        
    def get_items(self, state):
        if isinstance(self.source, list):
            return self.source
        elif callable(self.source):
            return self.source()
        else:
            raise ValueError("The datasource must be a list or a function that returns a list.")
        
        
class While(Step):
    def __init__(self, condition, steps):
        super().__init__("While")
        self.condition = condition
        self.steps = steps
        self.condition_description = self._describe_condition()

    def _describe_condition(self):
        if isinstance(self.condition, str):
            return self.condition
        elif isinstance(self.condition, Step):
            return "Repeat:"#f"Condition Step: {self.condition.name}"
        else:
            return "Unknown Condition"

    def list_steps(self,state):
        for step in self.steps:
            if isinstance(step, Var):
                step.execute(state,False)
                
        step_names = ["Repeat the following instructions:"] #[f"{self.name} (Condition: {self.condition_description})"]
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def execute(self, state):
        noema = ""
        while self.evaluate_condition(state):
             for step in self.steps:
                output = step.execute(state)
                if isinstance(step, GenStep):
                    noema += step.display_step_name + str(output) + "\n"                
                else:
                    noema += step.name + "\n"
                    
                if not isinstance(step, DebugStep) and not isinstance(step,FlowStep):
                    state.set_prop(step.name,output)

    def evaluate_condition(self, state):
        if callable(self.condition):
            try:
                return self.condition()
            except Exception as e:
                print(f"Error evaluating condition: {e}")
                return False
        elif isinstance(self.condition, Step):
            res = self.condition.execute(state)
            print(f"Condition result: {res}")
            return bool(res)
        else:
            raise ValueError("Condition must be either a lambda function or a Step.")