from .step import Step
from .memoir import Memoir

class Knowledge(Step):
    
    def __init__(self, value:str):
        super().__init__(name="Knowledge")
        self.value = value
        
    def execute(self, state):
        if isinstance(self.value, str):
            current_value = self.extract_variables_from_string(self.value, state)
        elif isinstance(self.value, Step):
            current_value = self.value.execute(state)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        
        fragments = state.memoir.retrieves(current_value, subject="knowledge")
        if len(fragments) > 0:
            current_value = fragments[0].value
        else:
            current_value = f"I know nothing about '{current_value}'."
        
        knowledge_to_insert = "#"+self.name.upper()+":"+ current_value + "\n"
        state.llm += knowledge_to_insert
        state.update_noema(knowledge_to_insert)
        return current_value
    
    def list_steps(self,state):
        return ["#"+self.name.upper()+": "+self.value] if self.should_include_in_list() else []
