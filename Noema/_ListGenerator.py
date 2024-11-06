from Noema._AtomicGenerator import AtomicGenerator
from Noema._noesis import *
from guidance import models, gen, select, capture
from Noema.cfg import *
from Noema._Generator import Generator
from Noema.generators import Int, Sentence, Word, Bool, Float

class ListGenerator(Generator):
    
    element_type = None
    
    def __init__(self,element_type):
        self.element_type = element_type
    
    def execute(self, noesis_model, state):
        llm = state.llm
        python_type = None
        if self.element_type == "Int":
            llm += noesis_model.value + "\n"
            llm += noesis_model.display_var() + capture(G.arrayOf(G.positive_num()), name="response")
            python_type = int
        if self.element_type == "Sentence":
            llm += noesis_model.value + "\n"
            llm += noesis_model.display_var() + " " + capture(G.arrayOf(G.alphaNumPunctForSentence()), name="response")
            python_type = str
        if self.element_type == "Word":
            llm += noesis_model.value + "\n"
            llm += noesis_model.display_var() + " " + capture(G.arrayOf(G.word()), name="response")
            python_type = str
        if self.element_type == "Bool":
            llm += noesis_model.value + "\n"
            llm += noesis_model.display_var() + " " + capture(G.arrayOf(G.bool()), name="response")
            python_type = bool
        if self.element_type == "Float":
            llm += noesis_model.value + "\n"
            llm += noesis_model.display_var() + " " + capture(G.arrayOf(G.float()), name="response")
            python_type = float
        
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + str(res) + "\n"
        res = res[1:-1].split(",")
        res = [python_type(el.strip()[1:-1]) for el in res]
        return res
    
    def to_string_name(self):
        return f"list[{self.element_type.__class__.__name__}]"
