from guidance import models, gen, select, capture
from Noema._Generator import Generator

class CustomGenerator(Generator):
    
    regex = None
    return_type = None
    stops = ["\n"]
    
    def execute(self, noesis_model, state):
        if self.regex is None or self.return_type is None:
            raise Exception("regex and return_type must be set in the CustomGenerator class")
        llm = state.llm
        print(noesis_model.value)
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + gen(regex=self.regex,name="response",stop_regex=" ", max_tokens=100) + "\n"
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)