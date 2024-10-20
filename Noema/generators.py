import re
from .step import GenStep,Step
from .cfg import *
from guidance import models, gen, select, capture


class Select(GenStep):
    
    def __init__(self, **kwargs):
        if len(kwargs) != 2:
            raise ValueError("Var must have 2 arguments, datasource and options.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        options = list(kwargs.values())[1]
        super().__init__(value, dest, output_type="Single Word")
        
        if callable(options):
            self.options = options
        elif isinstance(options, list):
            self.options = options
        elif isinstance(options, Step):
            self.options = options
        else:
            raise ValueError("The parameter must be a lambda function, a list or a Step.")
        self.display_type = "You respond by selecting the correct option."
                
    def execute(self, state):
        super().execute(state)    
        current_options = self.resolve_param(self.options, state) 
        llm = state.llm
        llm += self.display_step_name + self.current_llm_input+ " " + select(current_options, name="response")
        res = llm["response"]
        state.llm += self.display_step_name + res + "\n" 
        return res
    
    def resolve_param(self, param, state):
        if callable(param):
            return param()
        elif isinstance(param, Step):
            return param.execute(state)
        elif isinstance(param, list):
            return param
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        
    
class Word(GenStep):
    
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        super().__init__(value, dest, output_type="Single Word")
        self.display_type = "You respond with a single word."
        
    def execute(self, state):
        super().execute(state)    
        llm = state.llm    
        llm += self.display_step_name + self.current_llm_input + " The word is: " + capture(G.word(), name="res") + "\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        return res
    
class Sentence(GenStep):
    
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        super().__init__(value, dest, output_type="Sentence")
        self.display_type = "You respond with a sentence."

    def execute(self, state):
        super().execute(state) 
        llm = state.llm
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.sentence(), name="res") + ".\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        return res
    
class Int(GenStep):
    
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        super().__init__(value, dest, output_type="Int")
        self.display_type = "You respond with a number."

    def execute(self, state):
        super().execute(state)    
        llm = state.llm    
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.num(), name="res") + "\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        return int(res)
        
class Float(GenStep):
    
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        super().__init__(value, dest, output_type="Float")
        self.display_type = "You respond with a float number."

    def execute(self, state):
        super().execute(state)  
        llm = state.llm      
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.float(), name="res") + "\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        return float(res)
    
class Bool(GenStep):
    
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        super().__init__(value, dest, output_type="Bool")
        self.display_type = "You respond with a boolean."

    def execute(self, state):
        super().execute(state)   
        llm = state.llm     
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.bool(), name="res") + "\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        if res == "yes":
            res = True
        else:
            res = False
        return res
    
    

class ListOf(GenStep):
    
    def __init__(self, elementType:GenStep, **kwargs):
        if len(kwargs) != 1:
            raise ValueError("Var must have only one argument.")
        dest = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        super().__init__(value, dest, output_type="List")
        self.elementType = elementType
        
    def execute(self, state):
        super().execute(state)
        llm = state.llm
        if self.elementType is Word:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.word()), name="res") + "\n"    
        elif self.elementType is Sentence:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.sentence()), name="res") + "\n"
        elif self.elementType is Int:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.num()), name="res") + "\n"
        elif self.elementType is Float:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.float()), name="res") + "\n"
        elif self.elementType is Bool:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.bool()), name="res") + "\n"
        else:
            raise ValueError("The elementType must be a Word, Sentence, Int, Float or Bool.")
        
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        res = res[1:-1].split(",")
        res = [el.strip()[1:-1] for el in res]
        return res