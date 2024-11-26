
from guidance import models, gen, select, capture
from Noema._Generator import Generator

class AtomicGenerator(Generator):
    
    grammar = None
    return_type = None

    def execute(self, noesis_model, state, local_vars = None):
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.display_var() + " " + noesis_model.value + " " + capture(self.grammar(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)