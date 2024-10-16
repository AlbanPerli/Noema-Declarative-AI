from .step import Step

class Text(Step):
    
    def __init__(self, value:str, action=None):
        super().__init__(name="Information: ", action=action)
        self.value = value
        
    def execute(self, state):
        current_value = self.extract_variables_from_string(self.value, state)
        # append
        state.llm += current_value + "\n"
        state.set(self.name, "4")
        return current_value
    
    def list_steps(self,state):
        """Retourne la liste des steps à exécuter, ici c'est seulement un step"""
        return [self.name+" "+self.value] if self.should_include_in_list() else []
